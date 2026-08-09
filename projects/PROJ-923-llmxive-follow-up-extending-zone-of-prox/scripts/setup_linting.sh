#!/bin/bash
# Script to install and configure linting and formatting tools
# This script should be run after installing requirements.txt

set -e

echo "Installing pre-commit hooks..."
pip install pre-commit

echo "Installing ruff and black (if not already in requirements)..."
pip install ruff black

echo "Installing pre-commit hooks configuration..."
pre-commit install

echo "Linting and formatting setup complete."
echo "Run 'pre-commit run --all-files' to check all files."
