#!/bin/bash
# Setup script for linting and formatting tools
# This script ensures ruff and black are installed and configured

set -e

echo "Installing linting and formatting tools..."

# Install tools if not already installed via requirements.txt
pip install black ruff

echo "Checking configuration files..."
if [ ! -f "pyproject.toml" ]; then
    echo "Error: pyproject.toml not found in project root."
    exit 1
fi

if [ ! -f ".ruff.toml" ]; then
    echo "Error: .ruff.toml not found in project root."
    exit 1
fi

echo "Configuration files found."

echo "Running initial format check (dry run)..."
black --check --diff code/ || true
ruff check code/ || true

echo "Linting and formatting setup complete."
echo "To format code: black code/"
echo "To lint code: ruff check code/"