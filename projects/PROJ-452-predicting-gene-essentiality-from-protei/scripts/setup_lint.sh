#!/bin/bash
# Setup script to install linting and formatting tools
# Run from project root: bash scripts/setup_lint.sh

set -e

echo "Installing development dependencies for linting and formatting..."

if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3.11+ is required but not found."
    exit 1
fi

python_version=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "Detected Python version: $python_version"

# Check if pip is available
if ! python3 -m pip --version &> /dev/null; then
    echo "Error: pip is not installed or not in PATH."
    exit 1
fi

# Upgrade pip
python3 -m pip install --upgrade pip setuptools wheel

# Install dev dependencies
python3 -m pip install -e ".[dev]"

echo "Installing pre-commit hooks..."
python3 -m pre_commit install

echo "Linting and formatting tools configured successfully!"
echo ""
echo "Usage:"
echo "  Run linter:   ruff check ."
echo "  Run formatter: black ."
echo "  Run pre-commit: pre-commit run --all-files"
