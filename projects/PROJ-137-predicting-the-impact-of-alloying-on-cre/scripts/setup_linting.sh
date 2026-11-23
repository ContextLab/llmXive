#!/bin/bash
# Setup script for linting and formatting tools
# This script installs pre-commit hooks and validates the environment

set -e

echo "Installing pre-commit hooks..."

# Ensure pre-commit is installed
if ! command -v pre-commit &> /dev/null; then
    echo "pre-commit not found. Installing..."
    pip install pre-commit
fi

# Install the hooks
pre-commit install

echo "Linting and formatting tools configured successfully!"
echo "Run 'pre-commit run --all-files' to check all files."
echo "Run 'pre-commit run' to check staged files only."
