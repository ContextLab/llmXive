#!/bin/bash
# setup_venv.sh - Create virtual environment and install dependencies
#
# Usage: ./setup_venv.sh
#
# This script creates a virtual environment in .venv/ and installs
# all dependencies from requirements.txt.

set -e

echo "=== Setting up Python virtual environment ==="

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "Detected Python version: ${PYTHON_VERSION}"

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment in .venv/..."
    python3 -m venv .venv
else
    echo "Virtual environment already exists at .venv/"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip setuptools wheel

# Install dependencies from requirements.txt
if [ -f "requirements.txt" ]; then
    echo "Installing dependencies from requirements.txt..."
    pip install -r requirements.txt
else
    echo "WARNING: requirements.txt not found. Installing from pyproject.toml..."
    pip install -e ".[dev]"
fi

# Verify installation
echo ""
echo "=== Verifying key packages ==="
python3 -c "import numpy; print(f'numpy: {numpy.__version__}')"
python3 -c "import pandas; print(f'pandas: {pandas.__version__}')"
python3 -c "import numpyro; print(f'numpyro: {numpyro.__version__}')"
python3 -c "import networkx; print(f'networkx: {networkx.__version__}')"

echo ""
echo "=== Virtual environment setup complete ==="
echo "To activate the environment manually, run:"
echo "  source .venv/bin/activate"
echo ""
echo "To deactivate, run:"
echo "  deactivate"