import os
import sys
import subprocess
import shutil
import threading
import json
import locale
import time

# --- BOOTSTRAP (ÖN HAZIRLIK) ---
# Arayüz kütüphaneleri (GTK4/Libadwaita) yüklü değilse script çökmesin diye
# en başta bunları kontrol edip kuruyoruz.
def bootstrap_system():
    if os.geteuid() != 0:
        print("❌ Lütfen bu scripti 'sudo' ile çalıştırın!")
        sys.exit(1)

    distro = "linux"
    try:
        with open("/etc/os-release") as f:
            data = f.read().lower()
            if "fedora" in data: distro = "fedora"
            elif "ubuntu" in data or "debian" in data: distro = "debian"
            elif "arch" in data: distro = "arch"
    except: pass

    # Kritik paketlerin kontrolü (Gerekirse sessizce kurar)
    # Bu kısım GUI açılmadan önceki "Can Simidi"dir.
    if distro == "fedora":
        # Fedora'da 'dnf' Python API'si yerine subprocess kullanmak daha güvenlidir
        try:
            import gi
        except ImportError:
            print("⚙️  Gerekli arayüz kütüphaneleri yükleniyor (Fedora)...")
            subprocess.run(["dnf", "install", "-y", "python3-gobject", "gtk4", "libadwaita", "python3-psutil"], check=True)

    elif distro == "debian":
        try:
            import gi
        except ImportError:
            print("⚙️  Gerekli arayüz kütüphaneleri yükleniyor (Debian/Ubuntu)...")
            subprocess.run(["apt", "update"], check=True)
            subprocess.run(["apt", "install", "-y", "python3-gi", "python3-psutil", "libgtk-4-bin", "libadwaita-1-0", "gir1.2-adw-1"], check=True)

bootstrap_system()

# --- İMPORTLAR (Artık Güvenli) ---
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib

# --- KURULUM SABİTLERİ ---
INSTALL_DIR = "/opt/omen-control"
CONFIG_DIR = "/etc/omen-control"
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
SERVICE_FILE = "/etc/systemd/system/omen-control.service"
DESKTOP_FILE = "/usr/share/applications/omen-control.desktop"

# --- DİL SÖZLÜĞÜ ---
LANGS = {
    "tr": {
        "title": "Omen Kontrol Kurulumu",
        "welcome_title": "HP Cihaz Yapılandırma Aracı",
        "welcome_desc": "Bu araç, HP Victus/Omen cihazınızı Linux üzerinde tam performansla kullanmanız için sistemi hazırlar.",
        "step_select": "Kurulum Tercihleri",
        "step_select_desc": "Sisteme eklenecek bileşenleri seçin:",
        "lbl_nvidia": "NVIDIA Sürücüleri (Native)",
        "sub_nvidia": "Resmi depolardan tescilli sürücüleri kurar.",
        "lbl_update": "Sistemi Güncelle",
        "sub_update": "Kurulum öncesi tüm sistem paketlerini günceller.",
        "lbl_steam": "Steam (Native)",
        "sub_steam": "Resmi depolardan Steam istemcisini kurar.",
        "lbl_heroic": "Heroic Launcher (Native/COPR)",
        "sub_heroic": "Epic/GOG oyunları için başlatıcı (Yerel Paket).",
        "lbl_libs": "Oyun Kütüphaneleri",
        "sub_libs": "Gamemode, Lutris ve Wine bağımlılıkları.",
        "p_sys": "Adım 1/3: Sistem Hazırlığı",
        "d_sys": "Güncellemeler yapılıyor ve seçilen uygulamalar kuruluyor...",
        "p_driver": "Adım 2/3: Sürücü Derleme",
        "d_driver": "Kernel modülü derleniyor (Bu işlem kernel header dosyalarını kullanır)...",
        "p_app": "Adım 3/3: Omen Control",
        "d_app": "Uygulama dosyaları yerleştiriliyor ve servisler açılıyor...",
        "finish_title": "Kurulum Başarılı!",
        "finish_desc": "Tüm işlemler tamamlandı.\nKernel modülünün aktif olması için bilgisayarınızı yeniden başlatın.",
        "btn_next": "İleri >",
        "btn_start": "Kurulumu Başlat",
        "btn_close": "Kapat",
        "btn_retry": "Hata (Tekrar Dene)",
        "msg_error": "HATA",
        "log_start": ">>> İşlem başlatılıyor...",
        "log_copr": ">>> COPR Deposu etkinleştiriliyor (Heroic)..."
    },
    "en": {
        "title": "Omen Control Setup",
        "welcome_title": "HP Device Configuration Tool",
        "welcome_desc": "Prepares your HP Victus/Omen device for maximum performance on Linux.",
        "step_select": "Installation Preferences",
        "step_select_desc": "Select components to add:",
        "lbl_nvidia": "NVIDIA Drivers (Native)",
        "sub_nvidia": "Installs proprietary drivers from official repos.",
        "lbl_update": "Update System",
        "sub_update": "Updates all system packages before installation.",
        "lbl_steam": "Steam (Native)",
        "sub_steam": "Installs Steam client from official repos.",
        "lbl_heroic": "Heroic Launcher (Native/COPR)",
        "sub_heroic": "Launcher for Epic/GOG games (Native Package).",
        "lbl_libs": "Gaming Libraries",
        "sub_libs": "Dependencies for Gamemode, Lutris, and Wine.",
        "p_sys": "Step 1/3: System Prep",
        "d_sys": "Updating system and installing selected apps...",
        "p_driver": "Step 2/3: Driver Compilation",
        "d_driver": "Compiling kernel module (Uses kernel headers)...",
        "p_app": "Step 3/3: Omen Control",
        "d_app": "Deploying application files and enabling services...",
        "finish_title": "Installation Successful!",
        "finish_desc": "All tasks completed.\nPlease restart your computer to activate the kernel module.",
        "btn_next": "Next >",
        "btn_start": "Start Installation",
        "btn_close": "Close",
        "btn_retry": "Error (Retry)",
        "msg_error": "ERROR",
        "log_start": ">>> Process started...",
        "log_copr": ">>> Enabling COPR Repo (Heroic)..."
    }
}

SERVICE_CONTENT = f"""[Unit]
Description=Omen Control RGB Service
After=multi-user.target

[Service]
ExecStart=/usr/bin/python3 {INSTALL_DIR}/backend.py
Restart=always
User=root

[Install]
WantedBy=multi-user.target
"""

DESKTOP_CONTENT = f"""[Desktop Entry]
Name=Omen Control
Comment=HP Victus RGB Controller
Exec={INSTALL_DIR}/gui.py
Icon={INSTALL_DIR}/images/omen_logo.png
Terminal=false
Type=Application
Categories=Utility;Settings;
"""

class InstallWizard(Adw.ApplicationWindow):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        sys_lang = locale.getdefaultlocale()[0]
        self.lang_code = "tr" if sys_lang and "TR" in sys_lang.upper() else "en"
        self.txt = LANGS[self.lang_code]

        self.set_title(self.txt["title"])
        self.set_default_size(650, 600)
        self.set_resizable(False)
        Adw.StyleManager.get_default().set_color_scheme(Adw.ColorScheme.FORCE_DARK)

        self.distro = self.detect_distro()

        # Checkboxlar
        self.chk_update = Gtk.CheckButton(active=True) # Varsayılan: Güncelleme açık
        self.chk_nvidia = Gtk.CheckButton()
        self.chk_steam = Gtk.CheckButton()
        self.chk_heroic = Gtk.CheckButton()
        self.chk_libs = Gtk.CheckButton()

        self.pages = []
        self.current_page_idx = 0

        self.setup_ui()

    def detect_distro(self):
        try:
            with open("/etc/os-release") as f:
                data = f.read().lower()
                if "fedora" in data: return "fedora"
                elif "ubuntu" in data or "debian" in data: return "debian"
                elif "arch" in data: return "arch"
        except: pass
        return "linux"

    def setup_ui(self):
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_content(main_box)

        header = Adw.HeaderBar()
        header.set_show_end_title_buttons(True)
        main_box.append(header)

        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT)
        self.stack.set_transition_duration(400)
        self.stack.set_hexpand(True); self.stack.set_vexpand(True)
        main_box.append(self.stack)

        # --- SAYFA SIRALAMASI: Hoşgeldin -> Seçim -> Sistem Hazırlığı -> Sürücü -> Uygulama -> Bitiş
        self.add_page(self.create_welcome_page(), "welcome")

        self.ui_select = self.create_selection_page()
        self.add_page(self.ui_select["box"], "select")

        self.ui_sys = self.create_progress_page(self.txt["p_sys"], self.txt["d_sys"])
        self.add_page(self.ui_sys["box"], "sys_prep")

        self.ui_driver = self.create_progress_page(self.txt["p_driver"], self.txt["d_driver"])
        self.add_page(self.ui_driver["box"], "driver")

        self.ui_app = self.create_progress_page(self.txt["p_app"], self.txt["d_app"])
        self.add_page(self.ui_app["box"], "app")

        self.add_page(self.create_finish_page(), "finish")

        action_bar = Gtk.ActionBar()
        main_box.append(action_bar)

        self.btn_next = Gtk.Button(label=self.txt["btn_next"], css_classes=["suggested-action"])
        self.btn_next.set_size_request(160, -1)
        self.btn_next.connect("clicked", self.on_next)

        end_pack = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        end_pack.set_hexpand(True); end_pack.set_halign(Gtk.Align.END)
        end_pack.append(self.btn_next)
        action_bar.pack_end(end_pack)

    def add_page(self, widget, name):
        self.stack.add_named(widget, name)
        self.pages.append(name)

    def create_welcome_page(self):
        page = Adw.StatusPage()
        page.set_icon_name("system-software-install-symbolic")
        page.set_title(self.txt["welcome_title"])
        page.set_description(self.txt["welcome_desc"])
        return page

    def create_selection_page(self):
        scrolled = Gtk.ScrolledWindow()
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15, margin_top=20, margin_bottom=20, margin_start=40, margin_end=40)
        scrolled.set_child(box)

        box.append(Gtk.Label(label=self.txt["step_select"], css_classes=["title-2"], xalign=0))
        box.append(Gtk.Label(label=self.txt["step_select_desc"], css_classes=["body"], xalign=0))

        grp = Adw.PreferencesGroup()
        grp.add(self.create_row(self.txt["lbl_update"], self.txt["sub_update"], self.chk_update))
        grp.add(self.create_row(self.txt["lbl_nvidia"], self.txt["sub_nvidia"], self.chk_nvidia))
        box.append(grp)

        grp2 = Adw.PreferencesGroup(title="Gaming")
        grp2.add(self.create_row(self.txt["lbl_steam"], self.txt["sub_steam"], self.chk_steam))
        grp2.add(self.create_row(self.txt["lbl_heroic"], self.txt["sub_heroic"], self.chk_heroic))
        grp2.add(self.create_row(self.txt["lbl_libs"], self.txt["sub_libs"], self.chk_libs))
        box.append(grp2)
        return {"box": scrolled}

    def create_row(self, title, sub, chk):
        r = Adw.ActionRow(title=title, subtitle=sub)
        r.add_prefix(chk)
        return r

    def create_progress_page(self, title, desc):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15, margin_top=30, margin_bottom=30, margin_start=30, margin_end=30)
        box.append(Gtk.Label(label=title, css_classes=["title-2"], xalign=0))
        box.append(Gtk.Label(label=desc, css_classes=["body"], xalign=0, opacity=0.7))
        scrolled = Gtk.ScrolledWindow(hexpand=True, vexpand=True)
        scrolled.add_css_class("frame")
        log = Gtk.TextView(editable=False, monospace=True, wrap_mode=Gtk.WrapMode.WORD, bottom_margin=10, left_margin=10, top_margin=10)
        p = Gtk.CssProvider(); p.load_from_data(b"textview text { background-color: #101010; color: #33ff33; font-size: 11px; }")
        log.get_style_context().add_provider(p, Gtk.STYLE_PROVIDER_PRIORITY_USER)
        scrolled.set_child(log); box.append(scrolled)
        prog = Gtk.ProgressBar(); box.append(prog)
        return {"box": box, "log": log, "prog": prog, "buffer": log.get_buffer()}

    def create_finish_page(self):
        page = Adw.StatusPage()
        page.set_icon_name("object-select-symbolic")
        page.set_title(self.txt["finish_title"])
        page.set_description(self.txt["finish_desc"])
        return page

    def log(self, ui, text):
        buf = ui["buffer"]; end = buf.get_end_iter()
        buf.insert(end, text + "\n")
        ui["log"].scroll_to_mark(buf.create_mark(None, end, False), 0.0, True, 0.0, 1.0)

    def run_thread(self, task, ui):
        self.btn_next.set_sensitive(False)
        ui["prog"].set_fraction(0.1)
        def worker():
            try:
                task(ui)
                GLib.idle_add(ui["prog"].set_fraction, 1.0)
                GLib.idle_add(self.next_step)
            except Exception as e:
                GLib.idle_add(self.log, ui, f"\n{self.txt['msg_error']}: {e}")
                GLib.idle_add(ui["prog"].set_fraction, 0.0)
                GLib.idle_add(self.btn_next.set_sensitive, True)
                GLib.idle_add(self.btn_next.set_label, self.txt["btn_retry"])
        threading.Thread(target=worker, daemon=True).start()

    def run_cmd(self, cmd, ui):
        proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        while True:
            line = proc.stdout.readline()
            if not line and proc.poll() is not None: break
            if line: GLib.idle_add(self.log, ui, line.strip())
        if proc.returncode != 0: raise Exception(f"Exit Code: {proc.returncode}")

    def next_step(self):
        if self.current_page_idx < len(self.pages) - 1:
            self.current_page_idx += 1
            page_name = self.pages[self.current_page_idx]
            self.stack.set_visible_child_name(page_name)
            self.btn_next.set_sensitive(True)
            if page_name == "select": self.btn_next.set_label(self.txt["btn_start"])
            elif page_name == "sys_prep": self.run_thread(self.task_sys_prep, self.ui_sys)
            elif page_name == "driver": self.run_thread(self.task_driver, self.ui_driver)
            elif page_name == "app": self.run_thread(self.task_app, self.ui_app)
            elif page_name == "finish": self.btn_next.set_label(self.txt["btn_close"])

    def on_next(self, btn):
        if self.current_page_idx == len(self.pages) - 1: self.close()
        else: self.next_step()

    # --- YENİ BİRLEŞTİRİLMİŞ SİSTEM HAZIRLIK GÖREVİ ---
    def task_sys_prep(self, ui):
        GLib.idle_add(self.log, ui, self.txt["log_start"])

        # 1. Sistem Güncelleme ve Temel Araçlar (ZORUNLU)
        kernel = subprocess.check_output(['uname', '-r']).decode().strip()
        GLib.idle_add(self.log, ui, f">>> Kernel: {kernel}")

        # Fedora için Exit Code 2 Hatasını Çözen Kritik Kısım:
        if self.distro == "fedora":
            # Önce güncelleme (seçildiyse)
            if self.chk_update.get_active():
                self.run_cmd("dnf update -y", ui)

            # Gerekli derleme araçlarını kur (Update sonrası kernel değişebileceği için)
            # kernel-devel-$(uname -r) o an çalışan kernelin başlıklarını getirir.
            self.run_cmd(f"dnf install gcc make kernel-devel-{kernel} kernel-headers -y", ui)

        elif self.distro == "debian":
            if self.chk_update.get_active():
                self.run_cmd("apt update && apt upgrade -y", ui)
            self.run_cmd("apt install build-essential linux-headers-$(uname -r) -y", ui)

        elif self.distro == "arch":
            if self.chk_update.get_active():
                self.run_cmd("pacman -Syu --noconfirm", ui)
            self.run_cmd("pacman -S base-devel linux-headers --noconfirm", ui)

        # 2. Seçilen Ekstra Uygulamaların Kurulumu
        if self.chk_nvidia.get_active():
            if self.distro == "fedora": self.run_cmd("dnf install akmod-nvidia xorg-x11-drv-nvidia-cuda -y", ui)
            elif self.distro == "debian": self.run_cmd("apt install nvidia-driver firmware-misc-nonfree -y", ui)
            elif self.distro == "arch": self.run_cmd("pacman -S nvidia nvidia-utils --noconfirm", ui)

        if self.chk_steam.get_active():
            if self.distro == "fedora": self.run_cmd("dnf install steam -y", ui)
            elif self.distro == "debian": self.run_cmd("apt install steam -y", ui)

        if self.chk_heroic.get_active():
            # Heroic için Fedora'da COPR (Native Repo) kullanımı
            if self.distro == "fedora":
                GLib.idle_add(self.log, ui, self.txt["log_copr"])
                self.run_cmd("dnf install dnf-plugins-core -y", ui)
                self.run_cmd("dnf copr enable atim/heroic-games-launcher -y", ui)
                self.run_cmd("dnf install heroic-games-launcher -y", ui)
            elif self.distro == "arch":
                self.run_cmd("pacman -S heroic-games-launcher-bin --noconfirm", ui) # AUR helper varsa, yoksa uyarı verebilir.
            else:
                # Debian/Ubuntu için Native DEB çok karmaşık (URL değişiyor), Flatpak en güvenlisi.
                if shutil.which("flatpak"):
                    self.run_cmd("flatpak install flathub com.heroicgameslauncher.hgl -y", ui)

        if self.chk_libs.get_active():
            if self.distro == "fedora": self.run_cmd("dnf install gamemode lutris wine -y", ui)
            elif self.distro == "debian": self.run_cmd("apt install gamemode lutris wine -y", ui)
            elif self.distro == "arch": self.run_cmd("pacman -S gamemode lutris wine --noconfirm", ui)

    def task_driver(self, ui):
        GLib.idle_add(self.log, ui, self.txt["log_start"])
        cwd = os.path.join(os.path.dirname(os.path.abspath(__file__)), "driver")

        # Temizlik ve Derleme
        # Make clean hata verirse önemsemiyoruz (ilk kurulumda makefile olmayabilir)
        try: self.run_cmd(f"cd {cwd} && make clean", ui)
        except: pass

        # Derleme işlemi (Artık kernel-devel kesin yüklü olduğu için burası çalışacak)
        self.run_cmd(f"cd {cwd} && make", ui)

        try: self.run_cmd("rmmod hp-wmi", ui)
        except: pass

        self.run_cmd(f"cd {cwd} && insmod hp-wmi.ko", ui)

        # Sürücüyü kalıcı yap
        dest = f"/lib/modules/{os.uname().release}/kernel/drivers/platform/x86/"
        if not os.path.exists(dest): os.makedirs(dest) # Dizin yoksa oluştur

        self.run_cmd(f"cp {cwd}/hp-wmi.ko {dest}", ui)
        self.run_cmd("depmod -a", ui)

        # Modülün açılışta yüklenmesi için conf oluştur
        with open("/etc/modules-load.d/hp-wmi.conf", "w") as f:
            f.write("hp-wmi\n")

    def task_app(self, ui):
        GLib.idle_add(self.log, ui, self.txt["log_start"])
        if not os.path.exists(INSTALL_DIR): os.makedirs(INSTALL_DIR)
        if not os.path.exists(INSTALL_DIR + "/images"): os.makedirs(INSTALL_DIR + "/images")

        src = os.path.dirname(os.path.abspath(__file__))
        shutil.copy(f"{src}/backend.py", f"{INSTALL_DIR}/backend.py")
        shutil.copy(f"{src}/gui.py", f"{INSTALL_DIR}/gui.py")

        # Görseller varsa kopyala, yoksa hata verme
        for img in ["keyboard.png", "omen_logo.png", "setup1.png", "setup2.png", "app_screenshot.png"]:
            p = f"{src}/images/{img}"
            if os.path.exists(p): shutil.copy(p, f"{INSTALL_DIR}/images/{img}")

        os.chmod(f"{INSTALL_DIR}/backend.py", 0o755); os.chmod(f"{INSTALL_DIR}/gui.py", 0o755)

        if not os.path.exists(CONFIG_DIR): os.makedirs(CONFIG_DIR)
        os.chmod(CONFIG_DIR, 0o777)
        if not os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "w") as f:
                json.dump({"enabled": True, "mode": 0, "zone_colors": ["#FF0000"]*4, "bri": 1.0, "spd": 50, "power": "balanced"}, f)
        os.chmod(CONFIG_FILE, 0o666)

        with open(SERVICE_FILE, "w") as f: f.write(SERVICE_CONTENT)
        with open(DESKTOP_FILE, "w") as f: f.write(DESKTOP_CONTENT)

        self.run_cmd("systemctl daemon-reload", ui)
        self.run_cmd("systemctl enable --now omen-control.service", ui)

if __name__ == "__main__":
    app = Adw.Application(application_id="com.victus.setup")
    app.connect("activate", lambda a: InstallWizard(application=a).present())
    app.run(sys.argv)
