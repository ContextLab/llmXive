#!/bin/bash
# T001c: Initialize Python 3.11 virtual environment
# This script creates a virtual environment in `code/venv` using Python 3.11.
# It ensures the environment is ready for subsequent tasks (T002a, etc.)
# by installing the pinned dependencies.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${SCRIPT_DIR}/venv"
PYTHON_CMD="python3.11"

echo "Checking for Python 3.11..."
if ! command -v $PYTHON_CMD &> /dev/null; then
    echo "ERROR: Python 3.11 ($PYTHON_CMD) is not installed or not in PATH."
    echo "Please install Python 3.11 and ensure it is accessible via 'python3.11'."
    exit 1
fi

echo "Python 3.11 found: $(python3.11 --version)"

# Remove existing venv if present to ensure a clean state
if [ -d "$VENV_DIR" ]; then
    echo "Removing existing virtual environment at $VENV_DIR..."
    rm -rf "$VENV_DIR"
fi

echo "Creating virtual environment at $VENV_DIR..."
$PYTHON_CMD -m venv "$VENV_DIR"

echo "Activating virtual environment..."
source "$VENV_DIR/bin/activate"

echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies from requirements.txt if it exists
REQUIREMENTS_FILE="${SCRIPT_DIR}/requirements.txt"
if [ -f "$REQUIREMENTS_FILE" ]; then
    echo "Installing dependencies from $REQUIREMENTS_FILE..."
    pip install -r "$REQUIREMENTS_FILE"
else
    echo "WARNING: $REQUIREMENTS_FILE not found. Skipping dependency installation."
    echo "Please ensure requirements.txt is created (e.g., by T002a) before running scripts."
fi

echo "Virtual environment initialization complete."
echo "To activate manually later, run: source $VENV_DIR/bin/activate"
deactivate