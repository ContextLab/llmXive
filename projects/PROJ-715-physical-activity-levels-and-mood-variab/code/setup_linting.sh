#!/bin/bash
# Script to install and configure linting and formatting tools
# Run this from the code/ directory: bash setup_linting.sh

set -e

echo "Installing linting and formatting tools..."
pip install flake8 black isort pytest

echo "Verifying installations..."
flake8 --version
black --version
isort --version
pytest --version

echo "Linting and formatting tools configured successfully."
echo "Usage:"
echo "  Lint:   flake8 ."
echo "  Format: black ."
echo "  Sort imports: isort ."