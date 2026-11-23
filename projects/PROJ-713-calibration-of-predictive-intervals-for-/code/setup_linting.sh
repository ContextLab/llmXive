#!/bin/bash
# Setup script for linting and formatting tools
# This script installs dev dependencies and initializes configuration

set -e

echo "Installing development dependencies..."
pip install -r requirements.txt

echo "Verifying installation..."
flake8 --version
black --version
isort --version

echo "Linting and formatting tools configured successfully."
echo "Run 'flake8 code/' to check for linting issues."
echo "Run 'black code/' to format code."
echo "Run 'isort code/' to sort imports."
