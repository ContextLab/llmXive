#!/bin/bash
# Setup script to install linting and formatting tools
# This script should be run after installing requirements.txt
# to ensure all development dependencies are present.

set -e

echo "Installing linting and formatting tools..."

# Install black, flake8, isort, and their dependencies
# We use pip directly here to ensure they are available in the environment
pip install black flake8 isort

echo "Linting and formatting tools installed successfully."
echo "To run checks:"
echo "  black --check code/"
echo "  isort --check-only code/"
echo "  flake8 code/"

echo ""
echo "To auto-fix formatting:"
echo "  black code/"
echo "  isort code/"
