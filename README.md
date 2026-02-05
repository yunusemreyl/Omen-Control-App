<div align="center">
  <img src="images/app_logo.png" alt="HP Omen Control Logo" width="128" height="128" />

  # HP OMEN Control Center (Linux)

  **The Missing Control Center for HP Omen & Victus Laptops on Linux**

  [Features](#-features) •
  [Installation](#-installation) •
  [Compatibility](#-compatibility) •
  [Screenshots](#-screenshots)
</div>

---

## 📖 About The Project

**HP Omen Control Center** is a native Linux application designed to unlock the full potential of **HP Omen** and **Victus** series laptops.

It is an open-source alternative to the official **OMEN Gaming Hub**, providing:

- RGB lighting control  
- Thermal & system monitoring  
- GPU mode switching  

All wrapped in a modern, user-friendly interface.

---

## 👨‍💻 Credits & Acknowledgments

Lead Developer: yunusemreyl

GPU Backend: EnvyControl

RGB Research & Driver Inspiration: hp-laptop-rgb-controller

Kernel Module Reference: hp-omen-linux-module

## ✨ Features

- 🎨 **RGB Lighting Control**  
  4-Zone keyboard lighting with:
  - Static  
  - Breathing  
  - Wave  
  - Cycle effects

- 📊 **System Dashboard**  
  Real-time monitoring of:
  - CPU / GPU / RAM usage  
  - Temperatures  
  - Battery health

- 🎮 **GPU MUX Switch**  
  Switch between:
  - Hybrid  
  - Discrete  
  - Integrated  
  modes using **EnvyControl**

- 🛠️ **Universal Installer**  
  - DKMS support  
  - Automatic driver rebuilds on kernel updates  
  - Works across multiple distributions

---

## 🚀 Installation

Open a terminal and run:

```bash
git clone https://github.com/yunusemreyl/Omen-Control-App.git
cd Omen-Control-App
chmod +x install.sh
sudo ./install.sh
```

## 🗑️ Uninstallation
To completely remove the application and kernel driver:
```bash
cd Omen-Control-App
chmod +x uninstall.sh
sudo ./uninstall.sh
```

## Note:
The installer uses DKMS, so the RGB driver will automatically rebuild when you update your Linux kernel.

## 🐧 Compatibility
| Distribution         | Status     | Notes                     |
| -------------------- | ---------- | ------------------------- |
| Ubuntu 24.04 LTS     | ✅ Verified | Full support via `apt`    |
| Fedora 43+           | ✅ Verified | Full support via `dnf`    |
| Arch Linux / CachyOS | ✅ Verified | Full support via `pacman` |
| Zorin OS / Pop!_OS   | ✅ Verified | Native support            |


## 📸 Screenshots
<div align="center"> <img src="app_screenshots/1.png" width="45%" /> <img src="app_screenshots/2.png" width="45%" /> <br /> <img src="app_screenshots/3.png" width="45%" /> <img src="app_screenshots/4.png" width="45%" /> </div>

## ⚖️ Legal Disclaimer
<div align="center" style="border: 1px solid #444; padding: 15px; border-radius: 8px;">

This tool is an independent open-source project developed by
yunusemreyl
.

It is NOT affiliated with or endorsed by Hewlett-Packard (HP).

The software is provided “as is”, without warranty of any kind.

</div>

<div align="center"> <sub>Developed with ❤️ by <a href="https://github.com/yunusemreyl">yunusemreyl</a></sub> </div>
