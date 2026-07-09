#!/bin/bash
# Setup script for linting (flake8) and formatting (black) tools
# This script installs the necessary tools if they are not already present
# and configures the project directory.

set -e

echo "Checking for Python environment..."
if [ -d ".venv" ]; then
    echo "Using existing .venv"
    VENV_ACTIVATE=".venv/bin/activate"
elif [ -d "venv" ]; then
    echo "Using existing venv"
    VENV_ACTIVATE="venv/bin/activate"
else
    echo "No virtual environment found. Creating one..."
    python3 -m venv .venv
    VENV_ACTIVATE=".venv/bin/activate"
fi

source $VENV_ACTIVATE

echo "Installing linting and formatting tools..."
# Install flake8 and black. Using version constraints compatible with the project's Python version.
# Note: requirements.txt already lists specific versions for core libs, but linting tools are dev deps.
pip install --upgrade pip
pip install flake8 black

echo "Verifying installation..."
flake8 --version
black --version

echo "Linting and formatting tools configured successfully."
echo "To run flake8: flake8 code/"
echo "To run black: black code/"
echo "To fix formatting: black code/"
