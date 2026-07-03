# Script to initialize the Python 3.11 virtual environment for PROJ-152
# Usage: .\scripts\setup_venv.ps1

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$VenvDir = Join-Path $ProjectRoot ".venv"
$RequirementsFile = Join-Path $ProjectRoot "requirements.txt"

Write-Host ">>> Project Root: $ProjectRoot"
Write-Host ">>> Target Python: 3.11"

# Check if python3.11 exists
$PythonCmd = Get-Command python3.11 -ErrorAction SilentlyContinue
if (-not $PythonCmd) {
    Write-Host "ERROR: Python 3.11 is not installed or not in PATH." -ForegroundColor Red
    Write-Host "Please install python3.11 and try again."
    exit 1
}

# Create virtual environment
Write-Host ">>> Creating virtual environment at $VenvDir using python3.11..."
& python3.11 -m venv $VenvDir

# Activate and upgrade pip
Write-Host ">>> Upgrading pip..."
& "$VenvDir\Scripts\python.exe" -m pip install --upgrade pip setuptools wheel

# Install dependencies
if (Test-Path $RequirementsFile) {
    Write-Host ">>> Installing dependencies from requirements.txt..."
    & "$VenvDir\Scripts\python.exe" -m pip install -r $RequirementsFile
} else {
    Write-Host "WARNING: requirements.txt not found at $RequirementsFile. Skipping dependency installation." -ForegroundColor Yellow
    Write-Host "You may need to run 'pip install -r requirements.txt' manually."
}

Write-Host ">>> Virtual environment setup complete."
Write-Host ">>> To activate, run: .\$VenvDir\Scripts\Activate.ps1"