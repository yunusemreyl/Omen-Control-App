#!/bin/bash

# ==============================================================================
#  HP OMEN CONTROL CENTER - INSTALLER
#  Version: 4.3 (Production Grade & Secure)
#  Author: yunusemreyl
# ==============================================================================

# --- STRICT MODE ---
# -e: Hata olursa dur
# -u: Tanımsız değişken kullanırsan dur
# -o pipefail: Pipe (|) içindeki komutlardan biri hata verirse dur
set -euo pipefail

# --- SABİTLER ---
APP_NAME="hp-omen-control"
INSTALL_DIR="/opt/$APP_NAME"
BIN_LINK="/usr/local/bin/omen-control"
DESKTOP_FILE="/usr/share/applications/com.yyl.hpcontrolcenter.desktop"
SERVICE_NAME="com.yyl.hpcontrolcenter.service"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}"
DBUS_FILE="/etc/dbus-1/system.d/com.yyl.hpcontrolcenter.conf"
MODULES_LOAD_FILE="/etc/modules-load.d/hp-omen-rgb.conf"

DKMS_NAME="hp-omen-rgb"
DKMS_VER="1.0"

# Renkler
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# --- FONKSİYONLAR ---
log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

check_root() {
    if [ "$EUID" -ne 0 ]; then
        log_error "Lütfen root yetkisiyle çalıştırın: sudo ./install.sh"
        exit 1
    fi
}

print_banner() {
    echo -e "${BLUE}"
    echo "  __  __  _   _  _   _  _   _  ___  ___  __  __  ____  ___  __  __  _   "
    echo " (  )(  )( )_( )( )_( )( )_( )/ __)(  _)(  \/  )(  _ \(  ,\(  )(  )( )  "
    echo "  )(__)(  ) _ (  ) _ (  ) _ ( \__ \ ) _) )    (  )   / )  / )(__)(  )(__"
    echo " (______)(_) (_)(_) (_)(_) (_)(___/(___)(_/\/\_)(_)\_)(_)\_(______)(____)"
    echo "                                                                        "
    echo "           HP OMEN CONTROL CENTER | Installer v4.3                      "
    echo "                  Developed by yunusemreyl                              "
    echo "                                                                        "
    echo -e "${NC}"
}

# --- 1. SİSTEM ANALİZİ VE PAKETLER ---

install_dependencies() {
    log_info "Sistem analiz ediliyor..."
    
    if [ -f /etc/os-release ]; then source /etc/os-release; else log_error "OS Release okunamadı."; exit 1; fi

    KERNEL_VER=$(uname -r)
    # Header Fiziksel Kontrolü (DKMS öncesi garanti)
    HEADER_PATH="/lib/modules/$KERNEL_VER/build"

    log_info "Kernel: $KERNEL_VER ($ID)"

    case "$ID" in
        ubuntu|debian|linuxmint|pop|kali)
            log_info "Paket Yöneticisi: APT"
            apt-get update -qq
            apt-get install -y python3-venv python3-pip python3-dev libgtk-4-dev libadwaita-1-dev \
                build-essential linux-headers-"$KERNEL_VER" dkms git \
                libcairo2-dev libglib2.0-dev

            # Girepository: Önce yeniyi dene, olmazsa eskiyi kur (Ubuntu 24.10+ uyumu)
            if ! apt-get install -y libgirepository-2.0-dev 2>/dev/null; then
                log_info "Modern Girepository bulunamadı, Legacy (1.0) kuruluyor..."
                apt-get install -y libgirepository1.0-dev
            fi
            ;;

        fedora|nobara)
            log_info "Paket Yöneticisi: DNF"
            dnf install -y python3-gobject gtk4-devel libadwaita-devel cairo-gobject-devel gobject-introspection-devel \
                kernel-devel-"$KERNEL_VER" python3-pip dkms git gcc make python3-devel
            ;;

        arch|manjaro|cachyos|endeavouros)
            log_info "Paket Yöneticisi: PACMAN (Full Upgrade)"
            # Partial Upgrade riskini önlemek için -Syu kullanıldı
            pacman -Syu --noconfirm --needed python-gobject gtk4 libadwaita linux-headers python-pip dkms git base-devel gobject-introspection
            ;;
        
        *)
            log_error "Desteklenmeyen dağıtım: $ID"
            exit 1
            ;;
    esac

    # Header Dosyası Kontrolü (Kesin)
    if [ ! -d "$HEADER_PATH" ]; then
        log_error "Kernel header dosyaları '$HEADER_PATH' altında bulunamadı!"
        log_error "Sistemi güncelleyip yeniden başlatmanız gerekebilir."
        exit 1
    fi
}

# --- 2. VENV KURULUMU ---

setup_venv() {
    log_info "Sanal ortam (/opt altında) hazırlanıyor..."

    # Eski kurulumu temizle (Hata vermemesi için || true, çünkü set -e aktif)
    rm -rf "$INSTALL_DIR" || true
    mkdir -p "$INSTALL_DIR"

    python3 -m venv "$INSTALL_DIR/venv"
    "$INSTALL_DIR/venv/bin/pip" install --upgrade pip setuptools wheel

    log_info "Python kütüphaneleri derleniyor..."
    
    # pkg-config yolunu garantiye al
    export PKG_CONFIG_PATH="/usr/lib/pkgconfig:/usr/lib/x86_64-linux-gnu/pkgconfig:/usr/share/pkgconfig"

    "$INSTALL_DIR/venv/bin/pip" install pygobject pydbus
    "$INSTALL_DIR/venv/bin/pip" install git+https://github.com/bayasdev/envycontrol.git
}

# --- 3. DRIVER (DKMS) ---

setup_dkms() {
    log_info "Sürücü (DKMS) yapılandırılıyor..."
    
    dkms remove -m $DKMS_NAME -v $DKMS_VER --all &>/dev/null || true
    rm -rf "/usr/src/$DKMS_NAME-$DKMS_VER"
    mkdir -p "/usr/src/$DKMS_NAME-$DKMS_VER"

    if [ ! -f "driver/src/hp-omen-rgb.c" ]; then
        log_error "Sürücü kaynak dosyası (driver/src/hp-omen-rgb.c) eksik!"
        exit 1
    fi

    cp driver/src/hp-omen-rgb.c "/usr/src/$DKMS_NAME-$DKMS_VER/"

    cat > "/usr/src/$DKMS_NAME-$DKMS_VER/dkms.conf" <<EOF
PACKAGE_NAME="$DKMS_NAME"
PACKAGE_VERSION="$DKMS_VER"
BUILT_MODULE_NAME[0]="$DKMS_NAME"
DEST_MODULE_LOCATION[0]="/extra"
AUTOINSTALL="yes"
EOF

    cat > "/usr/src/$DKMS_NAME-$DKMS_VER/Makefile" <<EOF
obj-m += hp-omen-rgb.o
all:
	make -C /lib/modules/\$(shell uname -r)/build M=\$(PWD) modules
clean:
	make -C /lib/modules/\$(shell uname -r)/build M=\$(PWD) clean
EOF

    dkms add -m $DKMS_NAME -v $DKMS_VER
    dkms install -m $DKMS_NAME -v $DKMS_VER

    # Modern Autoload
    echo "$DKMS_NAME" > "$MODULES_LOAD_FILE"
    
    # Anlık yükleme (Hata verirse devam et, set -e yüzünden script patlamasın)
    modprobe $DKMS_NAME || log_warn "Modül şu an yüklenemedi. Reboot sonrası aktif olacaktır."
}

# --- 4. DOSYALAR ---

setup_files() {
    log_info "Uygulama dosyaları kopyalanıyor..."
    cp -r src "$INSTALL_DIR/"
    cp -r images "$INSTALL_DIR/"
    
    chmod +x "$INSTALL_DIR/src/daemon/omen_service.py"
    chmod +x "$INSTALL_DIR/src/gui/main_window.py"
}

# --- 5. SERVİS VE DBUS ---

setup_service() {
    log_info "Servis ve İzinler ayarlanıyor..."

    cat > $DBUS_FILE <<EOF
<!DOCTYPE busconfig PUBLIC "-//freedesktop//DTD D-BUS Bus Configuration 1.0//EN" "http://www.freedesktop.org/standards/dbus/1.0/busconfig.dtd">
<busconfig>
  <policy user="root">
    <allow own="com.yyl.hpcontrolcenter"/>
    <allow send_destination="com.yyl.hpcontrolcenter"/>
  </policy>
  <policy context="default">
    <allow send_destination="com.yyl.hpcontrolcenter"/>
    <allow receive_sender="com.yyl.hpcontrolcenter"/>
    <allow send_interface="com.yyl.hpcontrolcenter"/>
  </policy>
</busconfig>
EOF

    cat > $SERVICE_FILE <<EOF
[Unit]
Description=HP Omen Control Daemon (Venv)
After=multi-user.target

[Service]
Type=simple
WorkingDirectory=$INSTALL_DIR
Environment="PYTHONPATH=$INSTALL_DIR"
ExecStart=$INSTALL_DIR/venv/bin/python3 -m src.daemon.omen_service
Restart=always
User=root
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable $SERVICE_NAME
    systemctl restart $SERVICE_NAME
    
    # Modern D-Bus Reload
    log_info "D-Bus yeniden yükleniyor..."
    systemctl try-reload-or-restart dbus.service 2>/dev/null || true
}

# --- 6. KISAYOLLAR ---

setup_desktop_entry() {
    # Wrapper Script
    cat > $BIN_LINK <<EOF
#!/bin/bash
export PYTHONPATH="$INSTALL_DIR"
cd "$INSTALL_DIR"
exec "$INSTALL_DIR/venv/bin/python3" src/gui/main_window.py "\$@"
EOF
    chmod +x $BIN_LINK

    cat > $DESKTOP_FILE <<EOF
[Desktop Entry]
Name=HP Omen Control
Comment=Control RGB and GPU for HP Omen/Victus
Exec=$BIN_LINK
Icon=$INSTALL_DIR/images/app_logo.png
Terminal=false
Type=Application
Categories=Utility;Settings;System;
StartupNotify=true
EOF
    gtk-update-icon-cache /usr/share/icons/hicolor 2>/dev/null || true
}

# --- 7. GÜVENLİ UNINSTALLER OLUŞTURUCU ---

create_uninstaller() {
    local UNINSTALL_SCRIPT="$INSTALL_DIR/uninstall.sh"
    
    # Uninstall script içinde de Strict Mode ve Root Check var!
    cat > "$UNINSTALL_SCRIPT" <<EOF
#!/bin/bash
set -e

if [ "\$EUID" -ne 0 ]; then
   echo "Lütfen root yetkisiyle çalıştırın: sudo omen-uninstall"
   exit 1
fi

echo "Kaldırılıyor: HP Omen Control Center..."

systemctl stop $SERVICE_NAME || true
systemctl disable $SERVICE_NAME || true

# Dosya yoksa hata verme (-f)
rm -f $SERVICE_FILE
rm -f $DBUS_FILE
rm -f $DESKTOP_FILE
rm -f $BIN_LINK
rm -f $MODULES_LOAD_FILE

# DKMS Temizliği
dkms remove -m $DKMS_NAME -v $DKMS_VER --all || true

# Klasör Temizliği
rm -rf $INSTALL_DIR

systemctl daemon-reload
echo "Başarıyla kaldırıldı."
EOF
    chmod +x "$UNINSTALL_SCRIPT"
    ln -sf "$UNINSTALL_SCRIPT" "/usr/local/bin/omen-uninstall"
}

# --- MAIN ---

main() {
    check_root
    print_banner
    
    install_dependencies
    setup_venv
    setup_dkms
    setup_files
    setup_service
    setup_desktop_entry
    create_uninstaller
    
    echo -e "${GREEN}--------------------------------------------------${NC}"
    echo -e "${YELLOW}  KURULUM BAŞARIYLA TAMAMLANDI!${NC}"
    echo -e "  Uygulamayı başlatmak için: ${BLUE}omen-control${NC}"
    echo -e "  Kaldırmak için: ${RED}omen-uninstall${NC}"
    echo -e "${GREEN}--------------------------------------------------${NC}"
}

main
