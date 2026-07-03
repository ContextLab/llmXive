#!/bin/bash
set -e

# Project: PROJ-174-investigating-the-relationship-between-p
# Task: T002b - Setup Python 3.11 virtual environment and install dependencies

# Determine the directory where this script resides
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
CODE_DIR="$SCRIPT_DIR"

echo ">>> Setting up Python environment in $CODE_DIR..."

# Check for Python 3.11
if ! command -v python3.11 &> /dev/null; then
    echo "ERROR: Python 3.11 is not installed or not in PATH."
    echo "Please install Python 3.11 and try again."
    exit 1
fi

# Create virtual environment
VENV_PATH="$CODE_DIR/.venv"
if [ -d "$VENV_PATH" ]; then
    echo ">>> Virtual environment already exists at $VENV_PATH. Removing..."
    rm -rf "$VENV_PATH"
fi

echo ">>> Creating virtual environment with Python 3.11..."
python3.11 -m venv "$VENV_PATH"

# Activate and install
echo ">>> Activating environment and installing dependencies from requirements.txt..."
source "$VENV_PATH/bin/activate"

# Upgrade pip
pip install --upgrade pip --quiet

# Install requirements
if [ -f "$CODE_DIR/requirements.txt" ]; then
    pip install -r "$CODE_DIR/requirements.txt" --quiet
    echo ">>> Dependencies installed successfully."
else
    echo "ERROR: requirements.txt not found in $CODE_DIR"
    exit 1
fi

# Verify installation
echo ">>> Verifying key packages..."
python -c "import pandas, numpy, scipy, statsmodels, sklearn, mne, yaml, tqdm, cv2, requests, datasets, dotenv, radon; print('All packages imported successfully.')"

echo ">>> Setup complete. Activate with: source $VENV_PATH/bin/activate"
