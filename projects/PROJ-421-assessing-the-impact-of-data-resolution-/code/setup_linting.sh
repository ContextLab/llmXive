#!/bin/bash
# Setup script for linting and formatting tools (Ruff and Black)
# This script installs the necessary tools and initializes configuration files.

set -e

echo "Installing linting and formatting tools..."
pip install ruff black pre-commit

echo "Initializing pre-commit hooks..."
# Run pre-commit install to set up the git hook
# Note: This requires git to be initialized in the project root
if git rev-parse --git-dir > /dev/null 2>&1; then
    pre-commit install
    echo "Pre-commit hooks installed successfully."
else
    echo "Warning: Git repository not detected. Skipping 'pre-commit install'."
    echo "Run 'git init' and then 'pre-commit install' manually if needed."
fi

echo "Linting configuration complete."
echo "To run manually:"
echo "  ruff check code/"
echo "  ruff format code/"
echo "  black code/"
echo "  pre-commit run --all-files"