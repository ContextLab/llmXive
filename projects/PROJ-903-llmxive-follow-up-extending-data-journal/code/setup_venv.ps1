# PowerShell script to create a virtual environment and install dependencies for PROJ-903
# This script assumes requirements.txt is present in the project root.

$ErrorActionPreference = "Stop"

Write-Host "=== Setting up Python Virtual Environment for llmXive ==="

# Determine the project root (assuming this script is in code/)
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$VenvDir = Join-Path $ProjectRoot "venv"
$RequirementsFile = Join-Path $ProjectRoot "requirements.txt"

if (-not (Test-Path $RequirementsFile)) {
    Write-Host "Error: requirements.txt not found at $RequirementsFile" -ForegroundColor Red
    exit 1
}

Write-Host "Creating virtual environment at $VenvDir..."
python -m venv $VenvDir

Write-Host "Activating environment and installing dependencies from requirements.txt..."
# Activate venv
& "$VenvDir\Scripts\Activate.ps1"

# Upgrade pip
python -m pip install --upgrade pip

# Install requirements
python -m pip install -r $RequirementsFile

Write-Host "=== Setup Complete ==="
Write-Host "To activate the environment manually, run:"
Write-Host "  & '$VenvDir\Scripts\Activate.ps1'"
