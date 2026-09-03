#!/bin/bash
# Script to install linting and formatting dependencies if not already present
# Assumes a virtual environment is active or dependencies are installed via pip

set -e

echo "Installing linting and formatting tools..."

# Install ruff and black if not present
pip install --upgrade "ruff>=0.1.0" "black>=23.0.0" "flake8>=6.0.0"

echo "Linting environment setup complete."
echo "Run 'make lint' to check code style."
echo "Run 'make format' to auto-fix style issues."