#!/bin/bash
# setup_venv.sh
# Creates and activates a Python virtual environment for the project.
# Usage: source code/setup_venv.sh

set -e

# Determine the project root (assuming script is in code/)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
VENV_DIR="$PROJECT_ROOT/venv"

echo "Setting up virtual environment in: $VENV_DIR"

if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
else
    echo "Virtual environment already exists."
fi

echo "Installing dependencies from requirements.txt..."
source "$VENV_DIR/bin/activate"
pip install --upgrade pip
if [ -f "$PROJECT_ROOT/requirements.txt" ]; then
    pip install -r "$PROJECT_ROOT/requirements.txt"
else
    echo "Warning: requirements.txt not found at $PROJECT_ROOT/requirements.txt"
fi

echo "Virtual environment setup complete."
echo "To activate manually later, run: source $VENV_DIR/bin/activate"