#!/bin/bash
# Script to set up linting and formatting tools for the project

set -e

echo "Setting up linting and formatting tools..."

# Check if Python 3.11 is available
if ! command -v python3.11 &> /dev/null; then
    echo "Error: Python 3.11 is required but not found."
    echo "Please install Python 3.11 and ensure it is in your PATH."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3.11 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install development dependencies
echo "Installing development dependencies (ruff, black, pre-commit)..."
pip install -e ".[dev]"

# Install pre-commit hooks
echo "Installing pre-commit hooks..."
pre-commit install

echo ""
echo "Setup complete!"
echo ""
echo "You can now run:"
echo "  - 'ruff check .' to check for linting issues"
echo "  - 'ruff format .' to format code"
echo "  - 'black .' to format code (alternative to ruff format)"
echo "  - 'pre-commit run --all-files' to run all hooks on all files"
echo "  - 'pytest' to run tests"
echo ""
