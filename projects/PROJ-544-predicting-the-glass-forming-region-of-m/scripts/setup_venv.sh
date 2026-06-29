#!/bin/bash
# Script to initialize Python 3.11 virtual environment for PROJ-544
# Usage: ./scripts/setup_venv.sh

set -e

VENV_DIR=".venv"
REQUIREMENTS_FILE="requirements.txt"

echo "=== Setting up Python 3.11 virtual environment ==="

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}' | cut -d'.' -f1,2)
echo "Detected Python version: $PYTHON_VERSION"

if [[ ! "$PYTHON_VERSION" =~ ^3\.1[0-9] ]]; then
  echo "WARNING: Python 3.11+ recommended. Current version: $PYTHON_VERSION"
fi

# Remove existing venv if present
if [ -d "$VENV_DIR" ]; then
  echo "Removing existing virtual environment..."
  rm -rf "$VENV_DIR"
fi

# Create virtual environment
echo "Creating virtual environment in $VENV_DIR..."
python3 -m venv "$VENV_DIR"

# Activate and upgrade pip
echo "Upgrading pip..."
source "$VENV_DIR/bin/activate"
pip install --upgrade pip setuptools wheel

# Install dependencies
if [ -f "$REQUIREMENTS_FILE" ]; then
  echo "Installing dependencies from $REQUIREMENTS_FILE..."
  pip install -r "$REQUIREMENTS_FILE"
else
  echo "ERROR: $REQUIREMENTS_FILE not found!"
  exit 1
fi

echo ""
echo "=== Virtual environment setup complete ==="
echo "To activate, run: source $VENV_DIR/bin/activate"
echo "To deactivate, run: deactivate"
