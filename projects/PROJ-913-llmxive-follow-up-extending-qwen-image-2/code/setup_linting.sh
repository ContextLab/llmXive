#!/bin/bash
# Script to initialize linting and formatting tools for the project
# Usage: ./setup_linting.sh

set -e

echo "Checking for pip installation..."
if ! command -v pip &> /dev/null; then
    echo "pip could not be found. Please install Python and pip."
    exit 1
fi

echo "Installing linting and formatting dependencies..."
# Install ruff, black, flake8, and their dependencies
# Note: requirements.txt is managed by T002, but we ensure these specific tools are present
pip install --upgrade pip
pip install ruff black flake8

echo "Linting and formatting tools installed successfully."
echo ""
echo "To run Black (formatter):"
echo "  black code/"
echo ""
echo "To run Ruff (linter):"
echo "  ruff check code/"
echo ""
echo "To run Flake8 (linter):"
echo "  flake8 code/"
echo ""
echo "Configuration files (pyproject.toml, .ruff.toml, .flake8) are already present in the code/ directory."
