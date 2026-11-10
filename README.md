# ESP32 Toolbox

A collection of Windows utilities for ESP32 development, firmware flashing and working with Espressif's command-line tools.

ESP32 Toolbox packages graphical and console applications together with their Python source, bundled utilities and build scripts. The goal is to make common ESP32 workflows easier to access without having to assemble every command manually.

## What's included

| Component | What it does |
| --- | --- |
| **ESP32-Flasher** | Flash firmware images to ESP32 devices through a graphical or console application. |
| **ESP-Tools-Studio** | Provides a frontend for `esptool`, `espefuse` and `espsecure`. |
| **EXE Builder** | Contains the source and scripts used to build the included Windows executables. |

## ESP32-Flasher

ESP32-Flasher provides a Windows interface for flashing firmware to an ESP32 over a serial connection.

The GUI workflow lets you select a firmware `.bin` file, choose the serial COM port and start the flashing operation without manually assembling an `esptool` command.

Included distribution files:

- `ESP32-Flasher-GUI.exe`
- `ESP32-Flasher-Console.exe`
- Python source files for both interfaces.
- Bundled `esptool.exe`.
- ZIP distribution archive.

Use the console build when you want terminal output for troubleshooting or scripting.

## ESP-Tools-Studio

ESP-Tools-Studio provides a graphical frontend for three Espressif utilities:

| Utility | Main use |
| --- | --- |
| `esptool` | Detecting ESP devices and performing firmware and flash operations. |
| `espefuse` | Reading and programming ESP32 eFuses. |
| `espsecure` | Working with ESP firmware security and cryptographic operations. |

Two bundled tool versions are included:

- **5.5.0**
- **4.12.0**

The project provides GUI and console-enabled application builds, plus their Python source files. The console-enabled build is useful when you need to inspect command output while debugging.

## EXE Builder

The `exe-Builder/` directory contains the Python source and build scripts for the included applications.

Build targets are provided for:

| Application | Build |
| --- | --- |
| ESP32-Flasher | GUI |
| ESP32-Flasher | Console-enabled |
| ESP-Tools-Studio | GUI |
| ESP-Tools-Studio | Console-enabled |

The scripts are available in both `.bat` and `.cmd` formats.

Run the build script for the application variant you want to recreate. The source and required bundled tool files are kept alongside the build scripts.

## Running the applications

### Prebuilt applications

1. Download or clone this repository.
2. Extract the distribution archive if you are using a ZIP package.
3. Connect your ESP32 using a USB data cable.
4. Make sure Windows has a suitable USB-to-UART driver for the board.
5. Start the relevant executable.
6. Select the correct COM port and operation.

The prebuilt Windows executables are provided so you do not need to set up Python just to run the packaged applications.

### Building from source

The source files and individual build scripts are included in `exe-Builder/`. A Python environment and the dependencies required by the corresponding source files are needed to rebuild the applications.

## Repository layout

The repository is organized around three main directories:

```text
.
├── ESP32-Flasher/
│   ├── ESP32-Flasher-GUI.exe
│   ├── ESP32-Flasher-Console.exe
│   ├── Python source files
│   ├── esptool.exe
│   └── ZIP distribution
├── ESP-Tools-Studio/
│   ├── ESP-Tools-Studio-GUI.exe
│   ├── ESP-Tools-Studio-Console.exe
│   ├── Python source files
│   ├── esptool.exe
│   ├── espefuse.exe
│   ├── espsecure.exe
│   ├── version 4.12 utility executables
│   └── ZIP distribution
└── exe-Builder/
    ├── build scripts
    ├── Python source files
    ├── bundled utilities
    └── ZIP distribution
```

The exact contents may change as the tools are updated.

## Requirements

- Windows.
- An ESP32-compatible device.
- A working USB data cable.
- A serial COM port.
- A suitable USB-to-UART driver for your development board.

Python and build dependencies are required only when running or modifying the source directly or rebuilding the executables. They are not normally required for the prebuilt application packages.

## Git LFS

Large binary distributions, including executable and ZIP files, are tracked with Git Large File Storage (Git LFS). If a clone contains pointer files instead of the actual binaries, install Git LFS and pull the LFS objects:

```bash
git lfs install
git lfs pull
```

## Notes

- Select the correct COM port before starting a flash operation.
- Use a firmware image intended for your exact chip and board.
- eFuse operations can permanently change device configuration. Read the relevant Espressif documentation and verify every setting before applying changes.
- The bundled Espressif utilities are third-party software. Their authorship and licensing remain with Espressif.

## Project

**ESP32 Toolbox - a practical set of tools for getting ESP32 work done.** ⚡
