#!/bin/bash
# Script to install and configure linting and formatting tools
# Usage: bash scripts/setup_linting.sh

set -e

echo "Installing development dependencies..."
pip install -r requirements-dev.txt

echo "Installing pre-commit hooks..."
pre-commit install

echo "Linting and formatting configuration complete."
echo "Run 'pre-commit run --all-files' to verify the entire codebase."