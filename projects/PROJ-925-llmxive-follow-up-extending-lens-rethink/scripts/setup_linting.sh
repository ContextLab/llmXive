#!/bin/bash
# Script to install and configure linting and formatting tools
# Usage: ./scripts/setup_linting.sh

set -e

echo "Installing linting and formatting tools..."

# Install ruff (fast Python linter)
pip install ruff

# Install black (code formatter)
pip install black

# Install flake8 (optional, for legacy compatibility)
pip install flake8

# Verify installations
ruff --version
black --version
flake8 --version

echo "Linting and formatting tools installed successfully."
echo "Run 'black code/' to format code."
echo "Run 'ruff check code/' to check for linting errors."
echo "Run 'flake8 code/' for additional linting checks."
