#!/bin/bash
# Setup script for llmXive project virtual environment
# Usage: ./code/setup_virtualenv.sh

set -e  # Exit on any error

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="$PROJECT_ROOT/venv"
REQUIREMENTS_FILE="$PROJECT_ROOT/code/requirements.txt"

echo "=== llmXive Virtual Environment Setup ==="
echo "Project root: $PROJECT_ROOT"
echo "Virtualenv path: $VENV_DIR"

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "Detected Python version: $PYTHON_VERSION"

# Check if Python 3.10+ is installed
if [[ ! "$PYTHON_VERSION" =~ ^3\.(1[0-9]|[2-9][0-9]) ]]; then
    echo "ERROR: Python 3.10 or higher is required. Found: $PYTHON_VERSION"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ -d "$VENV_DIR" ]; then
    echo "Virtual environment already exists at $VENV_DIR. Removing..."
    rm -rf "$VENV_DIR"
fi

echo "Creating virtual environment..."
python3 -m venv "$VENV_DIR"

# Activate and upgrade pip
echo "Activating environment and upgrading pip..."
source "$VENV_DIR/bin/activate"
python -m pip install --upgrade pip setuptools wheel

# Install dependencies
if [ -f "$REQUIREMENTS_FILE" ]; then
    echo "Installing dependencies from $REQUIREMENTS_FILE..."
    pip install -r "$REQUIREMENTS_FILE"
else
    echo "WARNING: $REQUIREMENTS_FILE not found. Skipping dependency installation."
    echo "Please run 'pip install -r code/requirements.txt' manually."
fi

echo ""
echo "=== Setup Complete ==="
echo "To activate the environment manually, run:"
echo "  source $VENV_DIR/bin/activate"
echo ""
echo "To deactivate, run:"
echo "  deactivate"
echo ""
echo "Next steps:"
echo "  1. Activate the environment: source $VENV_DIR/bin/activate"
echo "  2. Run setup: python code/setup_directories.py"
echo "  3. Refer to code/README.md for further instructions"
