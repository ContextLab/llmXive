#!/bin/bash
set -e

# T002b: Initialize Python 3.11 virtual environment and install dependencies
# This script creates a venv at .venv and installs requirements.txt.

# Check for Python 3.11
if ! command -v python3.11 &> /dev/null; then
    echo "Error: Python 3.11 is required but not found. Please install python3.11."
    exit 1
fi

# Create virtual environment
echo "Creating Python 3.11 virtual environment..."
python3.11 -m venv .venv

# Activate and upgrade pip
echo "Activating environment and upgrading pip..."
source .venv/bin/activate
pip install --upgrade pip

# Install dependencies
if [ -f "requirements.txt" ]; then
    echo "Installing dependencies from requirements.txt..."
    pip install -r requirements.txt
else
    echo "Warning: requirements.txt not found. No dependencies installed."
fi

echo "Virtual environment setup complete."
echo "To activate: source .venv/bin/activate"