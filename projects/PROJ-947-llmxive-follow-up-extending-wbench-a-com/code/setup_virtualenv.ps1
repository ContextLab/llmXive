# Setup script for llmXive project virtual environment (Windows PowerShell)
# Usage: .\code\setup_virtualenv.ps1

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path | Split-Path -Parent
$VenvDir = Join-Path $ProjectRoot "venv"
$RequirementsFile = Join-Path $ProjectRoot "code\requirements.txt"

Write-Host "=== llmXive Virtual Environment Setup ==="
Write-Host "Project root: $ProjectRoot"
Write-Host "Virtualenv path: $VenvDir"

# Check Python version
try {
    $PythonVersion = python --version 2>&1
    Write-Host "Detected Python version: $PythonVersion"
} catch {
    Write-Host "ERROR: Python not found. Please install Python 3.10 or higher."
    exit 1
}

# Check if Python 3.10+ is installed
if ($PythonVersion -notmatch "Python 3\.(1[0-9]|[2-9][0-9])") {
    Write-Host "ERROR: Python 3.10 or higher is required. Found: $PythonVersion"
    exit 1
}

# Remove existing virtual environment if it exists
if (Test-Path $VenvDir) {
    Write-Host "Virtual environment already exists at $VenvDir. Removing..."
    Remove-Item -Recurse -Force $VenvDir
}

Write-Host "Creating virtual environment..."
python -m venv $VenvDir

# Activate and upgrade pip
Write-Host "Activating environment and upgrading pip..."
& "$VenvDir\Scripts\Activate.ps1"
python -m pip install --upgrade pip setuptools wheel

# Install dependencies
if (Test-Path $RequirementsFile) {
    Write-Host "Installing dependencies from $RequirementsFile..."
    pip install -r $RequirementsFile
} else {
    Write-Host "WARNING: $RequirementsFile not found. Skipping dependency installation."
    Write-Host "Please run 'pip install -r code\requirements.txt' manually."
}

Write-Host ""
Write-Host "=== Setup Complete ==="
Write-Host "To activate the environment manually, run:"
Write-Host "  $VenvDir\Scripts\Activate.ps1"
Write-Host ""
Write-Host "To deactivate, run:"
Write-Host "  deactivate"
Write-Host ""
Write-Host "Next steps:"
Write-Host "  1. Activate the environment: $VenvDir\Scripts\Activate.ps1"
Write-Host "  2. Run setup: python code\setup_directories.py"
Write-Host "  3. Refer to code\README.md for further instructions"