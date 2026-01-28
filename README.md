# HP Omen Control (Linux) 🐧

![Linux](https://img.shields.io/badge/Linux-FCC624?style=for-the-badge&logo=linux&logoColor=black)
![GTK4](https://img.shields.io/badge/GTK4-Libadwaita-green?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)

A Linux-compatible control and configuration tool for **HP Victus / Omen** laptops. This application brings power management, RGB keyboard control, and system monitoring together in a single, clean GTK4 interface. It serves as a lightweight, functional alternative to the Windows-only Omen Gaming Hub.

---

## 🖼️ Screenshots

| Installation Wizard | Installation Options | Main Control Panel (v2.1) |
| :---: | :---: | :---: |
| ![Setup 1](images/setup1.png) | ![Setup 2](images/setup2.png) | ![App Screenshot](images/app_screenshot.png) |

---

## ✨ Features

### 🔋 Power Profiles
* **ECO / Balanced / Performance** modes integrated with system power daemons.

### 🌡️ Live System Monitoring
* **CPU Temperature** tracking.
* **RAM and Disk** usage percentages.

### ⌨️ RGB Keyboard Control
* **Zone-based control** (Zone 1–4) or full keyboard synchronization.
* **Static color** selection and dynamic **Wave effects** (Right-to-Left).
* Fine-grained **Brightness and Speed** adjustments.

### 🧩 Setup Wizard (`setup.py`)
* Optional **NVIDIA driver** installation.
* **Gaming libraries** (Gamemode, Wine dependencies).
* **Steam and Heroic Games Launcher** support.

---

## 🚀 Quick Start & Installation

Tested on **Fedora 41**, **Ubuntu 24.04**, and **Arch Linux**. Copy and paste the command below to install:

```bash
git clone [https://github.com/yunusemreyl/Omen-Control-App.git](https://github.com/yunusemreyl/Omen-Control-App.git) && cd Omen-Control-App && sudo python3 setup.py
