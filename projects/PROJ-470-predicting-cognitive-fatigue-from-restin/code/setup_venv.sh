#!/bin/bash
# Script to initialize Python 3.11 virtual environment for PROJ-470
# Usage: bash code/setup_venv.sh
# Prerequisites: Python 3.11 must be installed and available in PATH

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="${PROJECT_ROOT}/venv"
REQUIREMENTS_FILE="${PROJECT_ROOT}/code/requirements.txt"

echo "=== Initializing Python 3.11 Virtual Environment ==="

# Check for Python 3.11
if ! command -v python3.11 &> /dev/null; then
    echo "Error: Python 3.11 is not installed or not in PATH."
    echo "Please install Python 3.11 and try again."
    exit 1
fi

# Remove existing venv if present
if [ -d "$VENV_DIR" ]; then
    echo "Removing existing virtual environment at $VENV_DIR..."
    rm -rf "$VENV_DIR"
fi

# Create virtual environment
echo "Creating virtual environment with Python 3.11..."
python3.11 -m venv "$VENV_DIR"

# Activate and upgrade pip
source "${VENV_DIR}/bin/activate"
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
if [ -f "$REQUIREMENTS_FILE" ]; then
    echo "Installing dependencies from $REQUIREMENTS_FILE..."
    pip install -r "$REQUIREMENTS_FILE"
else
    echo "Warning: requirements.txt not found at $REQUIREMENTS_FILE"
    echo "Dependencies not installed. Please install manually."
fi

echo "=== Virtual Environment Setup Complete ==="
echo "To activate the environment manually, run:"
echo "  source ${VENV_DIR}/bin/activate"
echo ""
echo "To verify installation, run:"
echo "  python -c \"import mne; import sklearn; import numpy; print('OK')\""
