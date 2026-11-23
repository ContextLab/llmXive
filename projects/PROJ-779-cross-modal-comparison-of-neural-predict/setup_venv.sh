#!/bin/bash
set -e

# Exit if .venv already exists to avoid redundant work
if [ -d ".venv" ]; then
    echo "Virtual environment .venv already exists. Skipping creation."
else
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate the virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip to latest version
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies from requirements.txt
if [ -f "requirements.txt" ]; then
    echo "Installing dependencies from requirements.txt..."
    pip install -r requirements.txt
else
    echo "ERROR: requirements.txt not found!"
    exit 1
fi

# Verify installation by listing packages
echo "Verifying installed packages..."
pip list

echo "Setup complete. Virtual environment is ready."
echo "To activate the environment manually, run: source .venv/bin/activate"