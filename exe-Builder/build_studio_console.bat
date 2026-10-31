@echo off
py -m PyInstaller --clean --onefile --console --name ESP-Tools-Studio-Console --add-binary "espefuse.exe;." --add-binary "espefuse_4.12.exe;." --add-binary "espsecure.exe;." --add-binary "espsecure_4.12.exe;." --add-binary "esptool.exe;." --add-binary "esptool_4.12.exe;." ESP-Tools-Studio-Console.py
pause