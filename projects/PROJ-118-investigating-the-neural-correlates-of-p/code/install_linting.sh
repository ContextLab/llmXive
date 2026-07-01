#!/bin/bash
set -e

# Ensure we are in the project root or code directory context
# The script is placed in code/ but assumes venv is at project root (one level up)
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PATH="${PROJECT_ROOT}/venv"

if [ ! -d "$VENV_PATH" ]; then
    echo "Error: Virtual environment not found at ${VENV_PATH}"
    echo "Please run T002 (Initialize Python 3.11 project) first."
    exit 1
fi

echo "Activating virtual environment..."
source "${VENV_PATH}/bin/activate"

echo "Installing linting and formatting tools (black, flake8, isort)..."
pip install --upgrade pip
pip install black flake8 isort

echo "Linting tools installed successfully."
echo "You can now run:"
echo "  black code/"
echo "  flake8 code/"
echo "  isort code/"
