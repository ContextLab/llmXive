#!/bin/bash
# Script to initialize a Python 3.11 virtual environment for the project.
# This script creates a venv in the 'code/venv' directory and installs
# initial dependencies from requirements.txt.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${SCRIPT_DIR}/venv"
REQUIREMENTS_FILE="${SCRIPT_DIR}/requirements.txt"

echo "=== Initializing Python 3.11 Virtual Environment ==="

# Check if Python 3.11 is available
if ! command -v python3.11 &> /dev/null; then
    echo "Error: Python 3.11 is not installed or not in PATH."
    echo "Please install Python 3.11 and try again."
    exit 1
fi

# Check if venv already exists
if [ -d "$VENV_DIR" ]; then
    echo "Virtual environment already exists at $VENV_DIR."
    echo "Removing existing environment..."
    rm -rf "$VENV_DIR"
fi

# Create the virtual environment
echo "Creating virtual environment with Python 3.11..."
python3.11 -m venv "$VENV_DIR"

# Activate and upgrade pip
echo "Upgrading pip, setuptools, and wheel..."
source "$VENV_DIR/bin/activate"
pip install --upgrade pip setuptools wheel

# Install dependencies if requirements.txt exists
if [ -f "$REQUIREMENTS_FILE" ]; then
    echo "Installing dependencies from requirements.txt..."
    pip install -r "$REQUIREMENTS_FILE"
else
    echo "Warning: requirements.txt not found. Skipping dependency installation."
fi

echo "=== Virtual Environment Ready ==="
echo "To activate manually, run: source ${VENV_DIR}/bin/activate"
echo "Python version: $(python --version)"
deactivate
echo "Script completed successfully."