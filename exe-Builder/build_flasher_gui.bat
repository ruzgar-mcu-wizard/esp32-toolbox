@echo off
py -m PyInstaller --clean --onefile --console --name ESP32-Flasher-GUI --add-binary "esptool.exe;." ESP32-Flasher-GUI.pyw
pause