#!/bin/bash
# Setup script for linting and formatting tools
# This script installs ruff and black if not already present

set -e

echo "Setting up linting and formatting tools..."

# Check if pip is available
if ! command -v pip &> /dev/null; then
    echo "Error: pip is not installed or not in PATH"
    exit 1
fi

# Install development dependencies
pip install -r requirements-dev.txt

echo "Linting and formatting tools installed successfully."
echo "Run 'ruff check . --fix' to fix linting issues."
echo "Run 'black .' to format code."
