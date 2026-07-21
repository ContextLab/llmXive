#!/bin/bash
# Setup script for linting and formatting tools
# This script installs the necessary tools and verifies their configuration

set -e

echo "Installing linting and formatting tools..."

# Install tools if not already present
pip install black flake8 isort pytest

echo "Verifying tool installation..."
black --version
flake8 --version
isort --version

echo "Checking configuration files..."
if [ -f "pyproject.toml" ]; then
    echo "pyproject.toml found."
else
    echo "Error: pyproject.toml not found!"
    exit 1
fi

if [ -f ".flake8" ]; then
    echo ".flake8 found."
else
    echo "Error: .flake8 not found!"
    exit 1
fi

if [ -f ".isort.cfg" ]; then
    echo ".isort.cfg found."
else
    echo "Error: .isort.cfg not found!"
    exit 1
fi

echo "Linting and formatting tools setup complete."
echo "You can now run:"
echo "  black code/ --check"
echo "  isort code/ --check"
echo "  flake8 code/"
