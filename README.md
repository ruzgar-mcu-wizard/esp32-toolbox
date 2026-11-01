# ESP32 Toolbox

**A collection of Windows-based tools for ESP32 firmware development, flashing, and device management.**

ESP32 Toolbox brings together several utilities designed to make working with ESP32 devices easier. It includes graphical applications, bundled Espressif utilities, and build scripts for producing standalone Windows executables.

The goal is to provide convenient access to common ESP32 development operations without having to manually work with individual command-line tools every time.

---

## Projects

### 1. ESP32-Flasher

A lightweight firmware flashing application for ESP32 devices.

ESP32-Flasher provides both graphical and console interfaces for flashing firmware to ESP32 microcontrollers.

**GUI version**
- Select a firmware `.bin` file.
- Select the serial COM port connected to the ESP32.
- Start the flashing process through a graphical interface.
- Avoid manually constructing esptool command-line arguments.

**Console version**
- Provides a console with the GUI based application for debugging.
- Useful for terminal-based workflows and scripting.

**Included files:**
- `ESP32-Flasher-GUI.exe`
- `ESP32-Flasher-Console.exe`
- Python source files for both interfaces.
- Bundled `esptool.exe`.
- A ZIP archive containing the project distribution.

---

### 2. ESP-Tools-Studio

A graphical and command-line frontend for Espressif's ESP32 development utilities.

Instead of manually remembering commands and arguments, ESP-Tools-Studio provides an application interface for working with three major Espressif tools:

| Utility | Purpose |
|---|---|
| **esptool** | Firmware flashing, chip detection, flash operations, and related ESP device operations. |
| **espefuse** | Reading and programming ESP32 eFuses. |
| **espsecure** | ESP firmware security and cryptographic operations. |

**Version support**

ESP-Tools-Studio includes two sets of bundled Espressif utilities:

- **Version 5.5.0**
- **Version 4.12.0**

This allows users to select between different tool versions when compatibility with a particular workflow matters.

**Available interfaces:**
- Graphical application (`ESP-Tools-Studio-GUI.exe`)
- Graphical application (With console for debugging.) (`ESP-Tools-Studio-Console.exe`)

The corresponding Python source files are included as well.

---

### 3. exe-Builder

A collection of build scripts and source files used to compile the applications into Windows executables.

The directory contains separate build scripts for each application and interface.

**Available build targets:**

| Application | Interface |
|---|---|
| ESP32-Flasher | GUI |
| ESP32-Flasher | GUI (With console) |
| ESP-Tools-Studio | GUI |
| ESP-Tools-Studio | GUI (With console) |

Each target has its own `.bat` and `.cmd` build script.

The directory also contains the Python source files and bundled Espressif utilities required by the build process.

This makes it possible to rebuild individual applications without having to manually assemble their build commands.

---

## Repository Structure

```text
ESP_Tool/
│
├── ESP32-Flasher/
│   ├── ESP32-Flasher-GUI.exe
│   ├── ESP32-Flasher-Console.exe
│   ├── ESP32-Flasher-GUI.pyw
│   ├── ESP32-Flasher-Console.py
│   ├── esptool.exe
│   └── ESP32-Flasher.zip
│
├── ESP-Tools-Studio/
│   ├── ESP-Tools-Studio-GUI.exe
│   ├── ESP-Tools-Studio-Console.exe
│   ├── ESP-Tools-Studio-GUI.pyw
│   ├── ESP-Tools-Studio-Console.py
│   ├── esptool.exe
│   ├── espefuse.exe
│   ├── espsecure.exe
│   ├── esptool_4.12.exe
│   ├── espefuse_4.12.exe
│   ├── espsecure_4.12.exe
│   └── ESP-Tools-Studio.zip
│
└── exe-Builder/
    ├── build_flasher_gui.cmd
    ├── build_flasher_console.cmd
    ├── build_studio_gui.cmd
    ├── build_studio_console.cmd
    ├── Python source files
    ├── Bundled Espressif utilities
    └── exe-Builder.zip
```

*The tree above illustrates the current distribution layout; individual files may change between releases.*

---

## Requirements

- Windows operating system.
- Appropriate USB-to-serial drivers for your ESP32 development board.
- A working USB data cable.
- Available serial COM port.
- Python and required build dependencies if building from source.

Prebuilt executables are included, so Python is not necessarily required to run the distributed applications.

---

## Building from Source

The `exe-Builder` directory contains individual scripts for building each application.

Build scripts are provided in both `.bat` and `.cmd` formats.

Run the corresponding script for the application and interface you want to build.

---

## Git LFS

Large binary files, including `.exe` and `.zip` distributions, are tracked using Git Large File Storage (Git LFS).

Source code and build scripts remain ordinary Git-tracked files.

---

## Project Goals

- Provide convenient ESP32 firmware flashing.
- Make Espressif command-line utilities easier to work with.
- Offer both graphical and console interfaces.
- Include multiple Espressif tool versions.
- Keep build scripts accessible and reproducible.
- Distribute ready-to-use Windows executables alongside their source files.

---

**ESP32 Toolbox — Tools for working with ESP32, without the unnecessary hassle.**
