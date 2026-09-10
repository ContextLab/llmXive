#!/bin/bash
# Setup script to install and configure linting and formatting tools
# This script ensures flake8, ruff, and black are installed and ready to use.

set -e

echo "Installing linting and formatting tools..."
pip install flake8 ruff black pre-commit

echo "Initializing pre-commit hooks..."
cd "$(dirname "$0")/.."
pre-commit install

echo "Linting and formatting tools configured successfully."
echo "Run 'pre-commit run --all-files' to check the entire codebase."