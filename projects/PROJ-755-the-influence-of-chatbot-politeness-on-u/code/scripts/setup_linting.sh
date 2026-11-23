#!/bin/bash
# Script to verify and install linting/formatting tools
# This script ensures ruff, black, and flake8 are available

set -e

echo "Checking for linting and formatting tools..."

# Check for ruff
if command -v ruff &> /dev/null; then
    echo "✓ ruff is installed: $(ruff --version)"
else
    echo "Installing ruff..."
    pip install ruff
fi

# Check for black
if command -v black &> /dev/null; then
    echo "✓ black is installed: $(black --version)"
else
    echo "Installing black..."
    pip install black
fi

# Check for flake8
if command -v flake8 &> /dev/null; then
    echo "✓ flake8 is installed: $(flake8 --version)"
else
    echo "Installing flake8..."
    pip install flake8
fi

echo "Linting tools verification complete."
echo "Run 'ruff check .' to lint the codebase."
echo "Run 'black .' to format the codebase."
