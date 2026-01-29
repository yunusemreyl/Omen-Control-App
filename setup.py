import os
import sys
import subprocess
import shutil
import threading
import json
import locale
import time
import random

# --- 1. EVRENSEL BOOTSTRAP ---
def bootstrap_system():
    if os.geteuid() != 0:
        print("❌ HATA: Bu scripti 'sudo' ile çalıştırmalısınız!")
        sys.exit(1)

    missing_libs = False
    try:
        import gi
        gi.require_version('Gtk', '4.0')
        gi.require_version('Adw', '1')
    except:
        missing_libs = True

    if missing_libs:
        print("⚙️  Sistem algılanıyor ve GUI kütüphaneleri kuruluyor...")
        if shutil.which("dnf"): # Fedora
            subprocess.run(["dnf", "install", "-y", "python3-gobject", "gtk4", "libadwaita", "python3-psutil", "mokutil"], check=False)
        elif shutil.which("apt"): # Debian/Ubuntu
            subprocess.run(["apt", "update"], check=False)
            subprocess.run(["apt", "install", "-y", "python3-gi", "python3-psutil", "libgtk-4-bin", "libadwaita-1-0", "gir1.2-adw-1", "mokutil"], check=False)
        elif shutil.which("pacman"): # Arch
            subprocess.run(["pacman", "-Sy", "--noconfirm", "python-gobject", "gtk4", "libadwaita", "python-psutil", "mokutil"], check=False)
        elif shutil.which("zypper"): # OpenSUSE
            subprocess.run(["zypper", "in", "-y", "python3-gobject", "gtk4", "libadwaita", "python3-psutil", "mokutil"], check=False)
        print("✅ Hazır. Arayüz açılıyor...")

bootstrap_system()

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib, Pango

# --- AYARLAR ---
INSTALL_DIR = "/opt/omen-control"
CONFIG_DIR = "/etc/omen-control"
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
SERVICE_FILE = "/etc/systemd/system/omen-control.service"
DESKTOP_FILE = "/usr/share/applications/omen-control.desktop"
SRC_DIR = os.path.dirname(os.path.abspath(__file__))

# --- EĞLENCELİ MESAJLAR LİSTESİ ---
FUN_MESSAGES = [
    "🐧 Penguenler besleniyor...",
    "🔥 RGB sıvıları dolduruluyor...",
    "🔧 Kernel modülleri ikna ediliyor...",
    "📦 Paketler kamyondan indiriliyor...",
    "☕ Kahve molası veriliyor (Şaka, çalışıyoruz)...",
    "🚀 HP Omen kalkışa hazırlanıyor...",
    "🐛 Böcekler (Bug) temizleniyor...",
    "💾 RAM indiriliyor (Keşke)...",
    "🎮 FPS değerleri hesaplanıyor...",
    "🧙‍♂️ Büyü yapılıyor...",
    "🧊 Fanlar kontrol ediliyor...",
    "💿 Windows anıları siliniyor..."
]

# --- DİL ---
LANGS = {
    "tr": {
        "title": "Omen Kontrol Kurulumu",
        "desc_welcome": "Bu araç HP cihazınızı Linux için yapılandırır ve gerekli oyun araçlarını kurar.",
        "lbl_select": "Kurulum Seçenekleri",
        "lbl_select_sub": "Sisteme kurulacak bileşenleri seçiniz:",
        "lbl_update": "Sistemi Güncelle",
        "sub_update": "Tüm paketleri günceller (Önerilir).",
        "lbl_nvidia": "Nvidia Sürücüleri",
        "sub_nvidia": "Resmi (Proprietary) sürücüler.",
        "lbl_steam": "Steam",
        "sub_steam": "Valve resmi istemcisi.",
        "lbl_heroic": "Heroic Launcher",
        "sub_heroic": "Epic/GOG oyunları için (Flatpak/Native).",
        "lbl_tools": "Oyun Araçları",
        "sub_tools": "MangoHud, Goverlay, GameMode, Lutris.",
        "btn_retry": "Tekrar Dene",
        "btn_skip": "Sorunu Atla ve Devam Et",
        "btn_next": "İleri >",
        "p_deps": "Adım 1/4: Kritik Bağımlılıklar",
        "d_deps": "GCC, Make ve Kernel Header dosyaları hazırlanıyor.",
        "p_apps": "Adım 2/4: Uygulamalar",
        "d_apps": "Seçilen oyun araçları ve yazılımlar kuruluyor.",
        "p_driver": "Adım 3/4: Sürücü (Driver)",
        "d_driver": "Kernel modülü derleniyor (Secure Boot KAPALI olmalı).",
        "p_final": "Adım 4/4: Tamamlama",
        "d_final": "Servisler etkinleştiriliyor.",
        "finish_desc": "Kurulum tamamlandı. Lütfen bilgisayarı YENİDEN BAŞLATIN.",
        "err_100": ">>> HATA: Şu an arka planda paket güncellemesi/indirmesi aktif.\n>>> Lütfen işlemin bitmesini bekleyin veya güncelleyiciyi kapatın."
    },
    "en": {
        "title": "Omen Control Setup",
        "desc_welcome": "Configure your HP device and install gaming tools.",
        "lbl_select": "Installation Options",
        "lbl_select_sub": "Select components to install:",
        "lbl_update": "Update System",
        "sub_update": "Updates all packages (Recommended).",
        "lbl_nvidia": "Nvidia Drivers",
        "sub_nvidia": "Official Proprietary drivers.",
        "lbl_steam": "Steam",
        "sub_steam": "Official Valve client.",
        "lbl_heroic": "Heroic Launcher",
        "sub_heroic": "For Epic/GOG games.",
        "lbl_tools": "Gaming Tools",
        "sub_tools": "MangoHud, Goverlay, GameMode, Lutris.",
        "btn_retry": "Retry",
        "btn_skip": "Skip Issue",
        "btn_next": "Next >",
        "p_deps": "Step 1/4: Dependencies",
        "d_deps": "Preparing GCC, Make, Kernel Headers.",
        "p_apps": "Step 2/4: Applications",
        "d_apps": "Installing selected tools.",
        "p_driver": "Step 3/4: Driver",
        "d_driver": "Compiling kernel module.",
        "p_final": "Step 4/4: Finalize",
        "d_final": "Enabling services.",
        "finish_desc": "Setup done. Please RESTART your computer.",
        "err_100": ">>> ERROR: Package manager is currently running.\n>>> Please wait for it to finish or close the updater."
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
        self.set_default_size(800, 700) # Biraz büyüttük
        Adw.StyleManager.get_default().set_color_scheme(Adw.ColorScheme.FORCE_DARK)

        self.resume_event = threading.Event()
        self.user_decision = None 
        self.fun_timer_id = None

        self.setup_ui()
        self.check_files()

    def check_files(self):
        req = ["backend.py", "gui.py", "driver"]
        missing = [f for f in req if not os.path.exists(os.path.join(SRC_DIR, f))]
        if missing:
            print(f"UYARI: Eksik dosyalar: {missing}")

    def setup_ui(self):
        main = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_content(main)

        header = Adw.HeaderBar()
        header.set_show_end_title_buttons(True)
        main.append(header)

        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT)
        self.stack.set_hexpand(True); self.stack.set_vexpand(True)
        main.append(self.stack)

        # Hoşgeldin
        wp = Adw.StatusPage(icon_name="system-run-symbolic", title=self.txt["title"])
        wp.set_description(self.txt["desc_welcome"])
        self.add_page(wp, "welcome")
        
        # Seçim
        self.ui_select = self.create_selection_page()
        self.add_page(self.ui_select["box"], "select")
        
        # İşlem Sayfaları
        self.ui_deps = self.create_progress_page(self.txt["p_deps"], self.txt["d_deps"])
        self.add_page(self.ui_deps["box"], "deps")

        self.ui_apps = self.create_progress_page(self.txt["p_apps"], self.txt["d_apps"])
        self.add_page(self.ui_apps["box"], "apps")

        self.ui_driver = self.create_progress_page(self.txt["p_driver"], self.txt["d_driver"])
        self.add_page(self.ui_driver["box"], "driver")

        self.ui_final = self.create_progress_page(self.txt["p_final"], self.txt["d_final"])
        self.add_page(self.ui_final["box"], "final")

        # Bitiş
        fp = Adw.StatusPage(icon_name="emblem-ok-symbolic", title="Tamamlandı", description=self.txt["finish_desc"])
        self.add_page(fp, "finish")

        # Butonlar
        act = Gtk.ActionBar()
        main.append(act)
        
        self.btn_skip = Gtk.Button(label=self.txt["btn_skip"], css_classes=["destructive-action"])
        self.btn_skip.set_visible(False)
        self.btn_skip.connect("clicked", lambda x: self.on_user_response("skip"))

        self.btn_next = Gtk.Button(label=self.txt["btn_next"], css_classes=["suggested-action"])
        self.btn_next.set_size_request(140, -1)
        self.btn_next.connect("clicked", self.on_next)

        box_btns = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        box_btns.append(self.btn_skip)
        box_btns.append(self.btn_next)
        act.pack_end(box_btns)

        self.pages = ["welcome", "select", "deps", "apps", "driver", "final", "finish"]
        self.curr_idx = 0

    def create_selection_page(self):
        scr = Gtk.ScrolledWindow()
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15, margin_top=20, margin_start=40, margin_end=40)
        scr.set_child(box)

        box.append(Gtk.Label(label=self.txt["lbl_select"], css_classes=["title-2"], xalign=0))
        box.append(Gtk.Label(label=self.txt["lbl_select_sub"], opacity=0.7, xalign=0))

        self.chk_update = Gtk.CheckButton(active=True)
        self.chk_nvidia = Gtk.CheckButton()
        self.chk_steam = Gtk.CheckButton()
        self.chk_heroic = Gtk.CheckButton()
        self.chk_tools = Gtk.CheckButton()

        g1 = Adw.PreferencesGroup(title="Sistem")
        g1.add(self.create_row(self.txt["lbl_update"], self.txt["sub_update"], self.chk_update))
        g1.add(self.create_row(self.txt["lbl_nvidia"], self.txt["sub_nvidia"], self.chk_nvidia))
        box.append(g1)

        g2 = Adw.PreferencesGroup(title="Oyun & Performans")
        g2.add(self.create_row(self.txt["lbl_steam"], self.txt["sub_steam"], self.chk_steam))
        g2.add(self.create_row(self.txt["lbl_heroic"], self.txt["sub_heroic"], self.chk_heroic))
        g2.add(self.create_row(self.txt["lbl_tools"], self.txt["sub_tools"], self.chk_tools))
        box.append(g2)
        return {"box": scr}

    def create_row(self, t, s, c):
        r = Adw.ActionRow(title=t, subtitle=s)
        r.add_prefix(c)
        return r

    def create_progress_page(self, title, desc):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10, margin_top=20, margin_start=20, margin_end=20)
        
        # Başlık Alanı
        box.append(Gtk.Label(label=title, css_classes=["title-2"], xalign=0))
        box.append(Gtk.Label(label=desc, opacity=0.7, xalign=0))
        
        # Terminal Görünümlü Log Alanı
        scr = Gtk.ScrolledWindow(hexpand=True, vexpand=True)
        scr.add_css_class("frame") # Çerçeve
        
        log = Gtk.TextView(editable=False, monospace=True, bottom_margin=10, left_margin=10, top_margin=10, right_margin=10)
        
        # CSS: Hacker Terminal Görünümü (Daha koyu siyah, parlak yeşil yazı)
        p = Gtk.CssProvider()
        css = b"""
        textview text {
            background-color: #0d0d0d;
            color: #33ff33;
            font-family: 'Monospace';
            font-size: 12px;
        }
        """
        p.load_from_data(css)
        log.get_style_context().add_provider(p, Gtk.STYLE_PROVIDER_PRIORITY_USER)
        
        scr.set_child(log)
        box.append(scr)
        
        # Eğlence ve Durum Alanı (Spinner + Fun Label)
        status_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        spinner = Gtk.Spinner()
        status_label = Gtk.Label(label="Hazır...", xalign=0)
        status_label.add_css_class("accent") # Renkli vurgu
        
        status_box.append(spinner)
        status_box.append(status_label)
        box.append(status_box)

        prog = Gtk.ProgressBar()
        box.append(prog)
        
        return {
            "box": box, 
            "log": log, 
            "prog": prog, 
            "buf": log.get_buffer(),
            "spinner": spinner,
            "status_lbl": status_label
        }

    def add_page(self, w, n): self.stack.add_named(w, n)

    # --- CORE ---
    def log(self, ui, text, error=False):
        buf = ui["buf"]
        end = buf.get_end_iter()
        
        # Tag kullanımı: Sadece hata varsa özel tag uygula
        if error:
            if not buf.get_tag_table().lookup("err"):
                 buf.create_tag("err", foreground="#ff5555", weight=700) # Kırmızı
            buf.insert_with_tags_by_name(end, f"{text}\n", "err")
        else:
            buf.insert(end, f"{text}\n")
            
        # Otomatik Kaydırma (En alta git)
        mark = buf.create_mark(None, buf.get_end_iter(), False)
        ui["log"].scroll_to_mark(mark, 0.0, True, 0.0, 1.0)

    def on_user_response(self, action):
        self.user_decision = action
        self.resume_event.set()

    def update_fun_message(self, ui):
        """Eğlenceli mesajları döndüren fonksiyon"""
        if ui["spinner"].get_spinning(): # Sadece işlem sürüyorsa
            msg = random.choice(FUN_MESSAGES)
            ui["status_lbl"].set_label(msg)
        return True # Timer devam etsin

    def on_next(self, btn):
        if self.btn_skip.get_visible():
            self.on_user_response("retry")
            return

        # Timer'ı durdur (varsa)
        if self.fun_timer_id:
            GLib.source_remove(self.fun_timer_id)
            self.fun_timer_id = None

        if self.curr_idx < len(self.pages) - 1:
            self.curr_idx += 1
            page = self.pages[self.curr_idx]
            self.stack.set_visible_child_name(page)
            
            mapping = {
                "deps": (self.task_deps, self.ui_deps),
                "apps": (self.task_apps, self.ui_apps),
                "driver": (self.task_driver, self.ui_driver),
                "final": (self.task_final, self.ui_final)
            }
            if page in mapping: self.start_thread(mapping[page][0], mapping[page][1])
            elif page == "finish":
                self.btn_next.set_label("Kapat" if self.lang_code == "tr" else "Close")
                self.btn_skip.set_visible(False)
        else: self.close()

    def start_thread(self, func, ui):
        self.btn_next.set_sensitive(False)
        self.btn_skip.set_visible(False)
        ui["prog"].set_fraction(0.1)
        ui["spinner"].start() # Spinner başlat
        
        # Eğlenceli mesaj timer'ını başlat
        self.fun_timer_id = GLib.timeout_add(3000, self.update_fun_message, ui)
        
        def runner():
            try:
                func(ui)
                GLib.idle_add(ui["prog"].set_fraction, 1.0)
                GLib.idle_add(ui["spinner"].stop) # Spinner durdur
                GLib.idle_add(ui["status_lbl"].set_label, "Tamamlandı.")
                GLib.idle_add(self.auto_next)
            except Exception as e:
                GLib.idle_add(self.log, ui, f"KRİTİK HATA: {e}", True)
                GLib.idle_add(ui["spinner"].stop)
        
        threading.Thread(target=runner, daemon=True).start()

    def auto_next(self):
        # Timer'ı temizle
        if self.fun_timer_id:
            GLib.source_remove(self.fun_timer_id)
            self.fun_timer_id = None
            
        self.btn_next.set_sensitive(True)
        self.on_next(None)

    def run_cmd(self, cmd, ui):
        while True:
            self.resume_event.clear()
            
            # Unbuffered output için stdbuf kullanımı (Mümkünse)
            # Ancak Python tarafında readline ile okuyoruz, bu yüzden anlık akış sağlarız.
            p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
            
            while True:
                line = p.stdout.readline()
                if not line and p.poll() is not None: break
                if line: GLib.idle_add(self.log, ui, line.strip())
            
            if p.returncode == 0: return True
            
            # HATA YÖNETİMİ
            if p.returncode == 100:
                GLib.idle_add(self.log, ui, self.txt["err_100"], True)
            else:
                GLib.idle_add(self.log, ui, f">>> HATA KODU: {p.returncode}", True)
            
            GLib.idle_add(self.log, ui, ">>> İŞLEM DURDURULDU. MÜDAHALE BEKLENİYOR...", True)
            
            GLib.idle_add(self.set_error_ui, True)
            self.resume_event.wait()
            GLib.idle_add(self.set_error_ui, False)
            
            if self.user_decision == "skip":
                GLib.idle_add(self.log, ui, ">>> ADIM ATLANDI ⏩", True)
                return False
            
            GLib.idle_add(self.log, ui, ">>> 🔄 Tekrar deneniyor...", False)

    def set_error_ui(self, active):
        self.btn_next.set_sensitive(True)
        self.btn_skip.set_visible(active)
        self.btn_next.set_label(self.txt["btn_retry"] if active else self.txt["btn_next"])
        if active: self.btn_next.add_css_class("destructive-action")
        else:
            self.btn_next.remove_css_class("destructive-action")
            self.btn_next.set_sensitive(False)

    # --- GÖREVLER ---
    def detect_mgr(self):
        if shutil.which("dnf"): return "dnf"
        if shutil.which("apt"): return "apt"
        if shutil.which("pacman"): return "pacman"
        if shutil.which("zypper"): return "zypper"
        return None

    def task_deps(self, ui):
        mgr = self.detect_mgr()
        GLib.idle_add(self.log, ui, f">>> Paket Yöneticisi: {mgr}")
        try:
            k_ver = subprocess.check_output(['uname', '-r']).decode().strip()
        except: k_ver = "unknown"
        
        cmds = []
        if mgr == "dnf":
            cmds.append("dnf update -y" if self.chk_update.get_active() else "true")
            cmds.append(f"dnf install -y gcc make kernel-devel-{k_ver} kernel-headers || dnf install -y gcc make kernel-devel kernel-headers")
        elif mgr == "apt":
            cmds.append("apt update" + (" && apt upgrade -y" if self.chk_update.get_active() else ""))
            cmds.append("apt install -y build-essential linux-headers-$(uname -r)")
        elif mgr == "pacman":
            cmds.append("pacman -Syu --noconfirm" if self.chk_update.get_active() else "true")
            cmds.append("pacman -S --noconfirm base-devel linux-headers")
        
        for c in cmds: self.run_cmd(c, ui)

    def task_apps(self, ui):
        mgr = self.detect_mgr()
        
        if self.chk_nvidia.get_active():
            if mgr == "dnf": self.run_cmd("dnf install -y akmod-nvidia", ui)
            elif mgr == "apt": self.run_cmd("apt install -y nvidia-driver", ui)
            elif mgr == "pacman": self.run_cmd("pacman -S --noconfirm nvidia nvidia-utils", ui)
        
        if self.chk_steam.get_active():
            if mgr == "dnf": self.run_cmd("dnf install -y steam", ui)
            elif mgr == "apt": self.run_cmd("apt install -y steam", ui)
            elif mgr == "pacman": self.run_cmd("pacman -S --noconfirm steam", ui)
        
        if self.chk_tools.get_active():
            GLib.idle_add(self.log, ui, ">>> Oyun araçları (MangoHud, Gamemode...) kuruluyor...")
            if mgr == "dnf":
                self.run_cmd("dnf install -y gamemode mangohud goverlay lutris wine", ui)
            elif mgr == "apt":
                self.run_cmd("apt install -y gamemode mangohud goverlay lutris wine", ui)
            elif mgr == "pacman":
                self.run_cmd("pacman -S --noconfirm gamemode mangohud goverlay lutris wine", ui)

        if self.chk_heroic.get_active():
            if shutil.which("flatpak"):
                self.run_cmd("flatpak install flathub com.heroicgameslauncher.hgl -y", ui)
            else:
                GLib.idle_add(self.log, ui, ">>> Flatpak bulunamadı, Heroic atlanıyor.", True)

    def task_driver(self, ui):
        try:
            if subprocess.call("mokutil --sb-state | grep -q enabled", shell=True) == 0:
                 GLib.idle_add(self.log, ui, ">>> UYARI: SECURE BOOT AÇIK! Sürücü yüklenmeyebilir.", True)
        except: pass

        cwd = os.path.join(SRC_DIR, "driver")
        if not os.path.exists(cwd):
            GLib.idle_add(self.log, ui, ">>> Driver klasörü yok, atlanıyor.", True)
            return

        if not self.run_cmd(f"cd {cwd} && make clean", ui): return
        if not self.run_cmd(f"cd {cwd} && make", ui): return
        
        self.run_cmd("rmmod hp-wmi || true", ui)
        if not self.run_cmd(f"cd {cwd} && insmod hp-wmi.ko", ui): 
             GLib.idle_add(self.log, ui, ">>> Modül yüklenemedi. Reboot sonrası çalışabilir.", True)

        dest = f"/lib/modules/{os.uname().release}/kernel/drivers/platform/x86/"
        if not os.path.exists(dest): os.makedirs(dest)
        self.run_cmd(f"cp {cwd}/hp-wmi.ko {dest}", ui)
        self.run_cmd("depmod -a", ui)
        with open("/etc/modules-load.d/hp-wmi.conf", "w") as f: f.write("hp-wmi\n")

    def task_final(self, ui):
        GLib.idle_add(self.log, ui, ">>> Dosyalar kopyalanıyor...")
        if not os.path.exists(INSTALL_DIR): os.makedirs(INSTALL_DIR)
        if not os.path.exists(INSTALL_DIR + "/images"): os.makedirs(INSTALL_DIR + "/images")

        try:
            shutil.copy(f"{SRC_DIR}/backend.py", f"{INSTALL_DIR}/backend.py")
            shutil.copy(f"{SRC_DIR}/gui.py", f"{INSTALL_DIR}/gui.py")
            img_src = os.path.join(SRC_DIR, "images")
            if os.path.exists(img_src):
                for f in os.listdir(img_src):
                    shutil.copy(os.path.join(img_src, f), os.path.join(INSTALL_DIR, "images", f))

            os.chmod(f"{INSTALL_DIR}/backend.py", 0o755)
            os.chmod(f"{INSTALL_DIR}/gui.py", 0o755)

            if not os.path.exists(CONFIG_DIR): os.makedirs(CONFIG_DIR)
            os.chmod(CONFIG_DIR, 0o777)
            if not os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, "w") as f:
                    json.dump({"enabled": True, "mode": 0, "zone_colors": ["#FF0000"]*4}, f)
            os.chmod(CONFIG_FILE, 0o666)

            with open(SERVICE_FILE, "w") as f: f.write(SERVICE_CONTENT)
            with open(DESKTOP_FILE, "w") as f: f.write(DESKTOP_CONTENT)

            self.run_cmd("systemctl daemon-reload", ui)
            self.run_cmd("systemctl enable --now omen-control.service", ui)
            GLib.idle_add(self.log, ui, ">>> BAŞARIYLA TAMAMLANDI.")

        except Exception as e:
            GLib.idle_add(self.log, ui, f"Kopyalama hatası: {e}", True)

if __name__ == "__main__":
    app = Adw.Application(application_id="com.victus.setup")
    app.connect("activate", lambda a: InstallWizard(application=a).present())
    app.run(sys.argv)
