#!/bin/bash
# Script to install pre-commit hooks
set -e

echo "Installing pre-commit hooks..."
python -m pip install --upgrade pre-commit
pre-commit install
echo "Pre-commit hooks installed successfully."
echo "Run 'pre-commit run --all-files' to check all files immediately."
