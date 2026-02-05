#!/bin/bash

# ==============================================================================
#  HP OMEN CONTROL CENTER - INSTALLER
#  Version: 3.2 (Universal & Clean)
#  Author: yunusemreyl
# ==============================================================================

# --- SABİTLER VE AYARLAR ---
APP_NAME="hp-omen-control"
APP_DIR="/usr/share/hp-omen-control"
BIN_LINK="/usr/local/bin/omen-control"
DESKTOP_FILE="/usr/share/applications/com.yyl.hpcontrolcenter.desktop"
SERVICE_NAME="com.yyl.hpcontrolcenter.service"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}"
DBUS_FILE="/etc/dbus-1/system.d/com.yyl.hpcontrolcenter.conf"

DKMS_NAME="hp-omen-rgb"
DKMS_VER="1.0"

# Renk Kodları
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# --- YARDIMCI FONKSİYONLAR ---

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_root() {
    if [ "$EUID" -ne 0 ]; then
        log_error "Lütfen bu scripti root yetkisiyle çalıştırın: sudo ./install.sh"
        exit 1
    fi
}

print_banner() {
    echo -e "${BLUE}"
    echo "#################################################"
    echo "#      HP OMEN CONTROL CENTER - INSTALLER       #"
    echo "#          v3.2 Universal | Clean Code          #"
    echo "#################################################"
    echo -e "${NC}"
}

# --- 1. DAĞITIM TESPİTİ VE BAĞIMLILIKLAR ---

install_dependencies() {
    log_info "Dağıtım tespit ediliyor ve paketler yükleniyor..."

    if [ -f /etc/os-release ]; then
        . /etc/os-release
    else
        log_error "Dağıtım bilgisi (/etc/os-release) okunamadı."
        exit 1
    fi

    # Fedora / Nobara / Bazzite Ailesi
    if [[ "$ID" == "fedora" || "$ID" == "nobara" || "$ID" == "bazzite" || "$ID_LIKE" == *"fedora"* ]]; then
        log_info "Sistem: Fedora/Nobara ($ID)"
        
        if [[ "$ID" == "bazzite" ]]; then
            log_warn "Bazzite (Immutable) tespit edildi. Sistem dosyalarına yazma işlemi başarısız olabilir."
        fi

        dnf install -y \
            python3-gobject \
            python3-pydbus \
            gtk4-devel \
            libadwaita-devel \
            kernel-devel-$(uname -r) \
            python3-pip \
            dkms \
            git \
            gcc \
            make

    # Debian / Ubuntu / Mint / Pop!_OS Ailesi
    elif [[ "$ID" == "ubuntu" || "$ID" == "debian" || "$ID_LIKE" == *"debian"* ]]; then
        log_info "Sistem: Debian/Ubuntu ($ID)"
        
        apt-get update
        apt-get install -y \
            python3-gi \
            python3-pydbus \
            libgtk-4-dev \
            libadwaita-1-dev \
            build-essential \
            linux-headers-$(uname -r) \
            python3-pip \
            dkms \
            git

    # Arch / Manjaro / CachyOS Ailesi
    elif [[ "$ID" == "arch" || "$ID" == "manjaro" || "$ID" == "cachyos" || "$ID_LIKE" == *"arch"* ]]; then
        log_info "Sistem: Arch/CachyOS ($ID)"
        
        pacman -Sy --noconfirm \
            python-gobject \
            gtk4 \
            libadwaita \
            linux-headers \
            python-pip \
            dkms \
            git \
            base-devel
        
        # Arch repolarında pydbus bazen eksik olabiliyor, pip ile garantiye alalım
        log_info "Python pydbus kontrol ediliyor..."
        pip3 install pydbus --break-system-packages 2>/dev/null || pip3 install pydbus

    else
        log_error "Desteklenmeyen dağıtım: $ID"
        log_warn "Manuel kurulum gereklidir."
        exit 1
    fi
}

install_envycontrol() {
    if ! command -v envycontrol &> /dev/null; then
        log_info "EnvyControl (bayasdev) yükleniyor..."
        # Modern pip versiyonları için --break-system-packages gerekebilir
        pip3 install git+https://github.com/bayasdev/envycontrol.git --break-system-packages 2>/dev/null || \
        pip3 install git+https://github.com/bayasdev/envycontrol.git
    else
        log_info "EnvyControl zaten yüklü."
    fi
}

# --- 2. DKMS SÜRÜCÜ KURULUMU ---

setup_dkms() {
    log_info "DKMS Sürücüsü yapılandırılıyor..."

    # Eski sürümü temizle
    dkms remove -m $DKMS_NAME -v $DKMS_VER --all &>/dev/null || true
    rm -rf "/usr/src/$DKMS_NAME-$DKMS_VER"
    mkdir -p "/usr/src/$DKMS_NAME-$DKMS_VER"

    # Kaynak kodu kopyala
    if [ -f "driver/src/hp-omen-rgb.c" ]; then
        cp driver/src/hp-omen-rgb.c "/usr/src/$DKMS_NAME-$DKMS_VER/"
    else
        log_error "Sürücü dosyası bulunamadı: driver/src/hp-omen-rgb.c"
        exit 1
    fi

    # dkms.conf oluştur
    cat > "/usr/src/$DKMS_NAME-$DKMS_VER/dkms.conf" <<EOF
PACKAGE_NAME="$DKMS_NAME"
PACKAGE_VERSION="$DKMS_VER"
BUILT_MODULE_NAME[0]="$DKMS_NAME"
DEST_MODULE_LOCATION[0]="/extra"
AUTOINSTALL="yes"
EOF

    # Makefile oluştur
    cat > "/usr/src/$DKMS_NAME-$DKMS_VER/Makefile" <<EOF
obj-m += hp-omen-rgb.o
all:
	make -C /lib/modules/\$(shell uname -r)/build M=\$(PWD) modules
clean:
	make -C /lib/modules/\$(shell uname -r)/build M=\$(PWD) clean
EOF

    # DKMS Build & Install
    log_info "Modül derleniyor (DKMS)..."
    dkms add -m $DKMS_NAME -v $DKMS_VER
    dkms build -m $DKMS_NAME -v $DKMS_VER
    
    if dkms install -m $DKMS_NAME -v $DKMS_VER; then
        log_info "Sürücü başarıyla kuruldu."
        modprobe $DKMS_NAME
        
        # Modülün açılışta yüklenmesi için ayar
        if ! grep -q "$DKMS_NAME" /etc/modules; then
            echo "$DKMS_NAME" >> /etc/modules
        fi
        
        # Arch/Systemd tabanlı sistemler için modules-load.d
        if [ -d "/etc/modules-load.d" ]; then
            echo "$DKMS_NAME" > /etc/modules-load.d/hp-omen-rgb.conf
        fi
    else
        log_error "DKMS kurulumu başarısız oldu. Kernel header paketlerini kontrol edin."
        # Scripti durdurmuyoruz, belki kullanıcı manuel halleder
    fi
}

# --- 3. DOSYA KOPYALAMA ---

setup_files() {
    log_info "Uygulama dosyaları kopyalanıyor..."
    
    mkdir -p "$APP_DIR"
    
    # Temiz kurulum için eskileri sil
    rm -rf "$APP_DIR/src" "$APP_DIR/images"
    
    cp -r src "$APP_DIR/"
    cp -r images "$APP_DIR/"
    
    # Çalıştırma izinleri
    chmod +x "$APP_DIR/src/daemon/omen_service.py"
    chmod +x "$APP_DIR/src/gui/main_window.py"
}

# --- 4. SERVİS VE DBUS AYARLARI ---

setup_service() {
    log_info "Systemd ve D-Bus yapılandırılıyor..."

    # D-Bus Politikası
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

    # Systemd Servis Dosyası
    cat > $SERVICE_FILE <<EOF
[Unit]
Description=HP Omen Control Daemon
After=multi-user.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 $APP_DIR/src/daemon/omen_service.py
Restart=always
User=root
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

    # Servisi aktif et
    systemctl daemon-reload
    systemctl enable $SERVICE_NAME
    systemctl restart $SERVICE_NAME
}

# --- 5. MASAÜSTÜ KISAYOLLARI ---

setup_desktop_entry() {
    log_info "Masaüstü kısayolları oluşturuluyor..."

    # /usr/local/bin wrapper
    cat > $BIN_LINK <<EOF
#!/bin/bash
/usr/bin/python3 $APP_DIR/src/gui/main_window.py "\$@"
EOF
    chmod +x $BIN_LINK

    # .desktop dosyası
    cat > $DESKTOP_FILE <<EOF
[Desktop Entry]
Name=HP Omen Control
Comment=Control RGB and GPU for HP Omen/Victus
Exec=$BIN_LINK
Icon=$APP_DIR/images/app_logo.png
Terminal=false
Type=Application
Categories=Utility;Settings;System;
StartupNotify=true
EOF

    # İkon önbelleğini güncelle
    gtk-update-icon-cache /usr/share/icons/hicolor 2>/dev/null || true
}

# --- MAIN LOOP ---

main() {
    check_root
    print_banner
    
    install_dependencies
    install_envycontrol
    setup_dkms
    setup_files
    setup_service
    setup_desktop_entry
    
    echo -e "${GREEN}--------------------------------------------------${NC}"
    echo -e "${YELLOW}  KURULUM TAMAMLANDI!${NC}"
    echo -e "  Komut: omen-control"
    echo -e "${GREEN}--------------------------------------------------${NC}"
}

# Scripti Başlat
main
