#!/bin/bash
# Script to initialize linting and formatting tools for the project.
# Usage: ./setup_linting.sh
#
# This script ensures black and ruff are installed and runs a quick
# validation to confirm configuration is recognized.

set -e

echo "Checking Python environment..."
python --version

echo "Installing development dependencies..."
pip install -e ".[dev]"

echo "Verifying Black configuration..."
black --check --diff code/utils/config.py || echo "Formatting check found differences (run 'black code/' to fix)"

echo "Verifying Ruff configuration..."
ruff check code/utils/config.py || echo "Linting check found issues (run 'ruff check --fix code/' to fix)"

echo "Setup complete. To format code: black code/"
echo "To lint code: ruff check code/"
echo "To auto-fix lint issues: ruff check --fix code/"