#!/bin/bash
# Script to ensure linting tools are installed and configured
# Run from the project root (code/)

set -e

echo "Checking for required tools..."

if ! command -v black &> /dev/null; then
    echo "Black not found. Installing..."
    pip install black
else
    echo "Black found: $(black --version)"
fi

if ! command -v ruff &> /dev/null; then
    echo "Ruff not found. Installing..."
    pip install ruff
else
    echo "Ruff found: $(ruff --version)"
fi

echo "Verifying configuration files..."
if [ -f "pyproject.toml" ]; then
    echo "pyproject.toml found."
else
    echo "ERROR: pyproject.toml not found!"
    exit 1
fi

if [ -f ".ruff.toml" ]; then
    echo ".ruff.toml found."
else
    echo "ERROR: .ruff.toml not found!"
    exit 1
fi

echo "Setup complete. Run 'scripts/format.sh' to format and lint."