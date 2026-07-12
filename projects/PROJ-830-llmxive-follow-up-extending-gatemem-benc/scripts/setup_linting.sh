#!/bin/bash
# Setup script for linting and formatting tools
# Ensures ruff and black are installed and configured

set -e

echo "Installing linting and formatting tools..."

# Install ruff and black if not already present
pip install ruff black

echo "Tools installed successfully."
echo "To check code: ruff check code/"
echo "To format code: black code/"
echo "To fix linting issues: ruff check --fix code/"
