#!/bin/bash
# Script to install dependencies for the llmXive project.
# This script assumes a Python 3.11+ environment is active.
# It installs packages from the requirements.txt file located in the project root.

set -e  # Exit immediately if a command exits with a non-zero status

echo "Installing dependencies from requirements.txt..."

# Check if requirements.txt exists
if [ ! -f "requirements.txt" ]; then
    echo "ERROR: requirements.txt not found in the current directory."
    exit 1
fi

# Upgrade pip first to ensure compatibility with newer package versions
python -m pip install --upgrade pip --quiet

# Install dependencies
# Using --quiet to reduce noise, but errors will still be shown
python -m pip install -r requirements.txt --quiet

echo "Dependencies installed successfully."
echo "Verifying installation..."

# Verify key packages are installed
python -c "import networkx; import pandas; import numpy; import scipy; import sklearn; import matplotlib; import seaborn; import yaml; import jsonschema; print('All core dependencies verified.')"

echo "Installation complete."