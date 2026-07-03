#!/bin/bash
# Setup script for Python 3.11 virtual environment
# This script creates a venv and installs dependencies from requirements.txt
# Usage: ./setup_venv.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_NAME="venv"
VENV_PATH="${SCRIPT_DIR}/${VENV_NAME}"

echo ">>> Checking Python 3.11 availability..."
if ! command -v python3.11 &> /dev/null; then
    echo "ERROR: Python 3.11 is required but not found."
    echo "Please install Python 3.11 and ensure it is in your PATH."
    exit 1
fi

PYTHON_VERSION=$(python3.11 --version)
echo ">>> Found: $PYTHON_VERSION"

echo ">>> Creating virtual environment at ${VENV_PATH}..."
python3.11 -m venv "${VENV_PATH}"

echo ">>> Activating virtual environment..."
source "${VENV_PATH}/bin/activate"

echo ">>> Upgrading pip, setuptools, and wheel..."
pip install --upgrade pip setuptools wheel

echo ">>> Installing dependencies from requirements.txt..."
if [ -f "${SCRIPT_DIR}/requirements.txt" ]; then
    pip install -r "${SCRIPT_DIR}/requirements.txt"
else
    echo "WARNING: requirements.txt not found. Skipping dependency installation."
    echo "Please run 'pip install -r requirements.txt' manually."
fi

echo ">>> Verifying installation..."
python -c "import transformers; import torch; import pandas; print('Core dependencies verified.')"

echo ""
echo "=========================================="
echo "Setup complete!"
echo "To activate the environment, run:"
echo "  source ${VENV_PATH}/bin/activate"
echo ""
echo "To deactivate, run:"
echo "  deactivate"
echo "=========================================="
