@echo off
py -m PyInstaller --clean --onefile --console --name ESP32-Flasher-Console --add-binary "esptool.exe;." ESP32-Flasher-Console.py
pause