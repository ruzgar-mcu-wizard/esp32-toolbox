@echo off
py -m PyInstaller --clean --onefile --windowed --name ESP-Tools-Studio-GUI --add-binary "espefuse.exe;." --add-binary "espefuse_4.12.exe;." --add-binary "espsecure.exe;." --add-binary "espsecure_4.12.exe;." --add-binary "esptool.exe;." --add-binary "esptool_4.12.exe;." ESP-Tools-Studio-GUI.pyw
pause