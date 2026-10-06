#!/bin/bash
# Setup script for linting and formatting tools
# This script installs flake8 and black if they are not already present
# and verifies the configuration files exist.

set -e

echo "Setting up linting and formatting tools..."

# Check if pip is available
if ! command -v pip &> /dev/null; then
    echo "Error: pip is not installed or not in PATH"
    exit 1
fi

# Install dev dependencies if not already present
echo "Installing flake8 and black..."
pip install --upgrade pip
pip install flake8 black

# Verify configuration files exist
if [ ! -f ".flake8" ]; then
    echo "Warning: .flake8 configuration file not found in current directory."
    echo "Please ensure .flake8 is present in the code/ directory."
fi

if [ ! -f "pyproject.toml" ]; then
    echo "Warning: pyproject.toml configuration file not found in current directory."
    echo "Please ensure pyproject.toml is present in the code/ directory."
fi

echo "Linting and formatting tools setup complete."
echo "To run flake8: flake8 code/src code/tests"
echo "To run black: black code/src code/tests"
echo "To run both: flake8 code/src code/tests && black --check code/src code/tests"