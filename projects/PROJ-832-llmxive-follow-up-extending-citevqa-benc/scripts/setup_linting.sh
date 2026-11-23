#!/bin/bash
# Setup script for linting (ruff) and formatting (black)
# This script ensures the tools are installed and provides basic configuration checks

set -e

echo "=== Setting up Linting and Formatting Tools ==="

# Check if virtual environment exists, if not create it
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install linting and formatting tools if not already present
echo "Installing ruff and black..."
pip install --upgrade pip
pip install ruff black

# Verify installation
echo "Verifying installations..."
ruff --version
black --version

# Run initial format check (dry run)
echo "Checking code formatting (dry run)..."
black --check --diff code/ || echo "Formatting issues found. Run 'black code/' to fix."

# Run initial lint check
echo "Running lint check..."
ruff check code/ || echo "Linting issues found. Run 'ruff check --fix code/' to fix."

echo "=== Setup Complete ==="
echo "To format code: black code/"
echo "To fix linting issues: ruff check --fix code/"
echo "To check formatting: black --check code/"
echo "To check linting: ruff check code/"
