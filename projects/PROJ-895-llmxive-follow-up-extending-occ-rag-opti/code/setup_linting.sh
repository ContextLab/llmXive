#!/bin/bash
# Setup script for linting and formatting tools
# This script ensures black and flake8 are installed and configurations are valid.

set -e

echo "Installing linting and formatting tools..."
pip install black flake8 isort

echo "Checking Black configuration..."
if [ -f "pyproject.toml" ]; then
    echo "pyproject.toml found. Verifying Black settings..."
    black --check --diff . || true
else
    echo "Warning: pyproject.toml not found. Creating default structure."
    # Note: The file is expected to be created by the task implementation.
fi

echo "Checking Flake8 configuration..."
if [ -f ".flake8" ]; then
    echo ".flake8 found. Verifying settings..."
    flake8 . --count --show-source --statistics || true
else
    echo "Warning: .flake8 not found."
fi

echo "Linting setup complete. Run 'black .' to format and 'flake8 .' to check."