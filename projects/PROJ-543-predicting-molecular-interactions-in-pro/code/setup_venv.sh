#!/usr/bin/env bash
# Setup Python 3.11 virtual environment for PROJ-543
# This script creates a venv in the `code/` directory using Python 3.11.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
VENV_DIR="$SCRIPT_DIR/venv"

echo ">>> Creating Python 3.11 virtual environment in $VENV_DIR..."

if [ ! -f "$ROOT_DIR/code/.python-version" ]; then
    # Check if pyenv is available and python 3.11 is installed
    if command -v pyenv &> /dev/null; then
        if ! pyenv versions | grep -q "3.11"; then
            echo ">>> Installing Python 3.11 via pyenv..."
            pyenv install 3.11.9
        fi
        echo "3.11.9" > "$ROOT_DIR/code/.python-version"
    fi
fi

# Attempt to create venv with python3.11, falling back to python3 if 3.11 is not found
if command -v python3.11 &> /dev/null; then
    PYTHON_CMD="python3.11"
elif command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
    # Verify python3 is 3.11
    if ! $PYTHON_CMD -c "import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)" 2>/dev/null; then
        echo ">>> Error: python3 is not version 3.11. Please install python3.11 or set PYTHON_CMD explicitly."
        exit 1
    fi
else
    echo ">>> Error: Python 3.11 (or python3) not found in PATH."
    exit 1
fi

echo ">>> Using Python interpreter: $($PYTHON_CMD --version)"
$PYTHON_CMD -m venv "$VENV_DIR"

echo ">>> Virtual environment created successfully at $VENV_DIR"
echo ">>> Activate with: source $VENV_DIR/bin/activate"
