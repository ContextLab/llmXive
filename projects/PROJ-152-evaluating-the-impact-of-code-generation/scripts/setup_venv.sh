#!/bin/bash
# Script to initialize the Python 3.11 virtual environment for PROJ-152
# Usage: ./scripts/setup_venv.sh

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="$PROJECT_ROOT/.venv"
REQUIREMENTS_FILE="$PROJECT_ROOT/requirements.txt"

echo ">>> Project Root: $PROJECT_ROOT"
echo ">>> Target Python: 3.11"

# Check if python3.11 exists
if ! command -v python3.11 &> /dev/null; then
    echo "ERROR: Python 3.11 is not installed or not in PATH."
    echo "Please install python3.11 and try again."
    exit 1
fi

# Create virtual environment
echo ">>> Creating virtual environment at $VENV_DIR using python3.11..."
python3.11 -m venv "$VENV_DIR"

# Activate and upgrade pip
echo ">>> Upgrading pip..."
source "$VENV_DIR/bin/activate"
pip install --upgrade pip setuptools wheel

# Install dependencies
if [ -f "$REQUIREMENTS_FILE" ]; then
    echo ">>> Installing dependencies from requirements.txt..."
    pip install -r "$REQUIREMENTS_FILE"
else
    echo "WARNING: requirements.txt not found at $REQUIREMENTS_FILE. Skipping dependency installation."
    echo "You may need to run 'pip install -r requirements.txt' manually."
fi

echo ">>> Virtual environment setup complete."
echo ">>> To activate, run: source $VENV_DIR/bin/activate"
