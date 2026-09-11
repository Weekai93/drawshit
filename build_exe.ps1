$ErrorActionPreference = "Stop"

python -m PyInstaller `
    --onefile `
    --name DrawShit `
    --clean `
    src/mouse_drawer.py

Write-Host "EXE erstellt: dist\DrawShit.exe"
