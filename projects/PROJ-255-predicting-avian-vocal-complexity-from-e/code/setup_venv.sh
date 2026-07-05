#!/bin/bash
# Setup virtual environment and install dependencies for PROJ-255
# This script creates a venv at .venv and installs requirements from requirements.txt

set -e

echo "=== Setting up Python virtual environment ==="

# Determine Python executable
if command -v python3 &> /dev/null; then
    PYTHON_CMD=python3
elif command -v python &> /dev/null; then
    PYTHON_CMD=python
else
    echo "Error: Python 3 or Python not found in PATH"
    exit 1
fi

echo "Using Python: $($PYTHON_CMD --version)"

# Create virtual environment
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment in .venv..."
    $PYTHON_CMD -m venv .venv
else
    echo "Virtual environment .venv already exists."
fi

# Activate and upgrade pip
echo "Activating virtual environment..."
source .venv/bin/activate

echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
if [ -f "requirements.txt" ]; then
    echo "Installing dependencies from requirements.txt..."
    pip install -r requirements.txt
else
    echo "Error: requirements.txt not found in project root"
    exit 1
fi

echo "=== Virtual environment setup complete ==="
echo "To activate manually later, run: source .venv/bin/activate"
