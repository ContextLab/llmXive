#!/bin/bash
# Setup script for linting and formatting tools
# Usage: ./scripts/setup_linting.sh

set -e

echo "Installing linting and formatting tools..."

# Install development tools
pip install black flake8 isort pre-commit pytest

# Initialize pre-commit hooks if not already done
if [ ! -d .git/hooks ]; then
    echo "Initializing git repository..."
    git init
fi

pre-commit install

echo "Linting setup complete!"
echo "Run 'pre-commit run --all-files' to check all files"
echo "Run 'black code/' to format code"
echo "Run 'flake8 code/' to check for style issues"
