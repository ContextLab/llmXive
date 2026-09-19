#!/bin/bash
# Script to verify and configure linting (ruff) and formatting (black)
# This script ensures the tools are installed and configuration files are valid.

set -e

echo "Checking Python version..."
python --version

echo "Installing/Upgrading linting and formatting tools..."
pip install -r requirements.txt

echo "Validating configuration files..."
# Check if ruff config exists
if [ -f ".ruff.toml" ]; then
    echo "Found .ruff.toml"
else
    echo "Error: .ruff.toml not found"
    exit 1
fi

# Check if black config exists
if [ -f ".black.toml" ]; then
    echo "Found .black.toml"
else
    echo "Error: .black.toml not found"
    exit 1
fi

echo "Linting configuration complete."
echo "You can now run:"
echo "  ruff check ."
echo "  black ."
echo "  pylint src/"
