#!/bin/bash
# Setup script to install and configure linting/formatting tools
# This script ensures ruff and black are installed and ready for use.

set -e

echo "Installing linting and formatting tools..."
pip install ruff black

echo "Running initial formatting check (dry-run)..."
black --check --diff code/ || echo "Note: Formatting differences detected. Run 'black code/' to fix."

echo "Running initial linting check..."
ruff check code/ || echo "Note: Linting issues detected. Run 'ruff check --fix code/' to fix."

echo "Linting and formatting configuration complete."
echo "To format code: black code/"
echo "To lint code: ruff check code/"
echo "To auto-fix linting issues: ruff check --fix code/"