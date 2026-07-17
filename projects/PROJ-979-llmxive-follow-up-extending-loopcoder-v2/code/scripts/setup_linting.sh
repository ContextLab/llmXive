#!/bin/bash
# Setup script to initialize linting and formatting tools
# Run from project root: bash code/scripts/setup_linting.sh

set -e

echo "Installing linting and formatting tools..."
pip install ruff black

echo "Running initial format check (dry run)..."
black --check code/ || echo "Note: Run 'black code/' to format code."

echo "Running initial lint check (dry run)..."
ruff check code/ || echo "Note: Run 'ruff check --fix code/' to fix issues."

echo "Linting and formatting setup complete."
echo "To format code: black code/"
echo "To fix lint issues: ruff check --fix code/"
echo "To check formatting: black --check code/"
echo "To check linting: ruff check code/"