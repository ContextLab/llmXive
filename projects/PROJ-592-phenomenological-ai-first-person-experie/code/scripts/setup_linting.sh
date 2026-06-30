#!/bin/bash
# Setup script to install and configure linting (ruff) and formatting (black) tools.
# This script should be run after installing dependencies via requirements.txt.

set -e

echo "Installing linting and formatting tools..."

# Install ruff and black if not already present
pip install ruff black

echo "Linting and formatting tools installed successfully."
echo "To format code: black code/"
echo "To lint code: ruff check code/"
echo "To fix linting issues: ruff check --fix code/"
echo "To check formatting: black --check code/"
