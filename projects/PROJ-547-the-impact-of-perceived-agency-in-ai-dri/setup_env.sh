#!/usr/bin/env bash
set -e

# ------------------------------------------------------------
# Virtual environment setup script for the PROJ-547 project.
# Creates a Python 3.11 virtual environment in the .venv
# directory and installs all required dependencies.
# ------------------------------------------------------------

# Name of the virtual environment directory
VENV_DIR=".venv"

# Create the virtual environment if it does not exist
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment in $VENV_DIR ..."
    python3 -m venv "$VENV_DIR"
else
    echo "Virtual environment already exists at $VENV_DIR"
fi

# Activate the virtual environment
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

# Upgrade pip to the latest version
echo "Upgrading pip ..."
pip install --upgrade pip

# Install required packages from requirements.txt
if [ -f "requirements.txt" ]; then
    echo "Installing dependencies from requirements.txt ..."
    pip install -r requirements.txt
else
    echo "Error: requirements.txt not found."
    exit 1
fi

echo "Setup complete. To activate the environment later, run:"
echo "  source $VENV_DIR/bin/activate"
echo "Happy coding!"