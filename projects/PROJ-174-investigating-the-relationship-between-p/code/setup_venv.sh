#!/bin/bash
# Script to setup Python 3.11 virtual environment and install dependencies
# for the llmXive research project.

set -e

# Check for Python 3.11
if ! command -v python3.11 &> /dev/null; then
    echo "ERROR: Python 3.11 is required but not found."
    echo "Please install Python 3.11 and ensure it is in your PATH."
    exit 1
fi

# Determine the directory where this script resides
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
VENV_DIR="$SCRIPT_DIR/venv"

echo "Creating Python 3.11 virtual environment at $VENV_DIR..."
python3.11 -m venv "$VENV_DIR"

echo "Activating virtual environment..."
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

echo "Upgrading pip..."
pip install --upgrade pip

if [ -f "$SCRIPT_DIR/requirements.txt" ]; then
    echo "Installing dependencies from requirements.txt..."
    pip install -r "$SCRIPT_DIR/requirements.txt"
else
    echo "WARNING: requirements.txt not found in $SCRIPT_DIR. Skipping dependency installation."
fi

echo "Virtual environment setup complete."
echo "To activate the environment, run: source $VENV_DIR/bin/activate"
