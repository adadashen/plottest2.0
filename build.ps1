Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Write-Host "== Build data-analysis-tool (Windows) ==" -ForegroundColor Cyan

if (-not (Test-Path ".venv")) {
  Write-Host "Creating venv..." -ForegroundColor Yellow
  py -3 -m venv .venv
}

Write-Host "Activating venv..." -ForegroundColor Yellow
& .\.venv\Scripts\Activate.ps1

Write-Host "Installing deps..." -ForegroundColor Yellow
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install pyinstaller

Write-Host "Cleaning dist/build..." -ForegroundColor Yellow
if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }
if (Test-Path "build") { Remove-Item -Recurse -Force "build" }

Write-Host "Running PyInstaller..." -ForegroundColor Yellow
pyinstaller .\packaging\windows\analysis_tool.spec

Write-Host ""
Write-Host "Done. Output:" -ForegroundColor Green
Write-Host "  dist\data-analysis-tool.exe"

