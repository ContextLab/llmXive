#!/bin/bash
# Install linting and formatting tools
set -e

echo "Installing linting tools..."
pip install ruff black flake8

echo "Linting tools installed."
echo "Run 'bash scripts/format.sh' to format code."
echo "Run 'bash scripts/lint.sh' to check for linting issues."