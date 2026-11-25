# kaf-cli-gui one-shot packaging (Windows PowerShell)
param([string]$KafCliUrl = 'https://github.com/ystyle/kaf-cli/releases/latest/download/kaf-cli_v1.3.16_windows_amd64.zip')
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot

# 1) python deps
python -m pip install --upgrade pyinstaller pillow

# 2) kaf-cli.exe
if (-not (Test-Path '.\kaf-cli.exe')) {
    if ($KafCliUrl) {
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        Invoke-WebRequest -Uri $KafCliUrl -OutFile 'kaf-cli-win.zip'
        Expand-Archive 'kaf-cli-win.zip' -DestinationPath '.\tmp-kaftool' -Force
        Copy-Item '.\tmp-kaftool\kaf-cli.exe' '.\kaf-cli.exe' -Force
        Remove-Item 'kaf-cli-win.zip', '.\tmp-kaftool' -Recurse -Force
        Write-Host "kaf-cli.exe downloaded from $KafCliUrl"
    } else {
        throw 'Please place kaf-cli.exe in this directory first, or pass -KafCliUrl'
    }
}

# 3) build onedir (do NOT use onefile: bootloader cannot extract temp files in constrained sandboxes)
python -m PyInstaller --clean -y --onedir --windowed --name kaf-cli-gui kaf_gui.py

# 4) layout: app folder + kaf-cli.exe alongside (GUI finds it in APP_DIR or APP_DIR.parent)
if (Test-Path '.\dist\kaf-cli-gui') { Remove-Item '.\dist\kaf-cli-gui' -Recurse -Force }
Copy-Item '.\dist\kaf-cli-gui' '.\kaf-cli-gui' -Recurse
Copy-Item '.\kaf-cli.exe' '.\kaf-cli-gui\kaf-cli.exe' -Force
Write-Host 'Done: launch .\kaf-cli-gui\kaf-cli-gui.exe'
