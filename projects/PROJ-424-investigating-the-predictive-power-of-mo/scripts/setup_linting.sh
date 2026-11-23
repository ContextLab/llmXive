#!/bin/bash
set -e

echo "Setting up linting and formatting tools..."

# Install pre-commit if not present
if ! command -v pre-commit &> /dev/null; then
    echo "Installing pre-commit..."
    pip install pre-commit
fi

# Install pre-commit hooks
echo "Installing git hooks..."
pre-commit install

echo "Linting and formatting setup complete."
echo "Run 'pre-commit run --all-files' to check all files."