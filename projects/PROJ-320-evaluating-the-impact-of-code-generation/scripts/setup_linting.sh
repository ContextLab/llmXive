#!/bin/bash
# Setup script for linting and formatting tools
# This script installs pre-commit hooks for ruff and black

set -e

echo "Installing pre-commit hooks..."

# Check if pre-commit is installed
if ! command -v pre-commit &> /dev/null; then
    echo "Installing pre-commit..."
    pip install pre-commit
fi

# Install the git hook
pre-commit install

echo "Linting and formatting tools configured successfully!"
echo "Run 'pre-commit run --all-files' to check all files."
echo "Run 'pre-commit run' to check staged files only."
