#!/bin/bash
# Setup script for Python 3.11 virtual environment
# This script creates a virtual environment and installs dependencies.

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
VENV_DIR="$SCRIPT_DIR/venv"

echo "Checking for Python 3.11..."
if command -v python3.11 &> /dev/null; then
    PYTHON_CMD="python3.11"
elif command -v python3 &> /dev/null; then
    # Check version
    VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    if [[ "$VERSION" == "3.11" ]]; then
        PYTHON_CMD="python3"
    else
        echo "Error: Python 3.11 is required but not found."
        echo "Please install python3.11 and ensure it is in your PATH."
        exit 1
    fi
else
    echo "Error: Python 3.11 is required but not found."
    echo "Please install python3.11 and ensure it is in your PATH."
    exit 1
fi

echo "Found Python: $PYTHON_CMD ($($PYTHON_CMD --version))"

if [ -d "$VENV_DIR" ]; then
    echo "Virtual environment already exists at $VENV_DIR. Removing..."
    rm -rf "$VENV_DIR"
fi

echo "Creating virtual environment at $VENV_DIR..."
$PYTHON_CMD -m venv "$VENV_DIR"

echo "Activating virtual environment and upgrading pip..."
source "$VENV_DIR/bin/activate"
pip install --upgrade pip setuptools wheel

echo "Installing dependencies from requirements.txt..."
if [ -f "$SCRIPT_DIR/requirements.txt" ]; then
    pip install -r "$SCRIPT_DIR/requirements.txt"
else
    echo "Warning: requirements.txt not found. Skipping dependency installation."
fi

echo "Virtual environment setup complete."
echo "To activate manually later, run: source $VENV_DIR/bin/activate"
