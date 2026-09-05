#!/bin/bash
# Setup script for linting and formatting tools
# Run: bash scripts/setup_linting.sh

set -e

echo "Installing development tools..."
pip install black ruff pre-commit

echo "Initializing pre-commit hooks..."
pre-commit install

echo "Running initial format check on all files..."
black --check code/ || echo "Code needs formatting. Run 'black code/' to fix."
ruff check code/ || echo "Code has linting issues. Run 'ruff check --fix code/' to fix."

echo "Setup complete. Remember to run 'pre-commit install' if not done automatically."