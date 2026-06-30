#!/bin/bash
# Setup script for linting and formatting tools
# Usage: bash code/setup_linting.sh

set -e

echo "Installing linting and formatting tools..."
pip install -r code/requirements.txt

echo "Verifying installation..."
python -m ruff --version
python -m black --version

echo "Running initial format check on code/..."
python -m black --check code/ || echo "Formatting issues found. Run 'python -m black code/' to fix."

echo "Running initial lint check on code/..."
python -m ruff check code/ || echo "Linting issues found. Run 'python -m ruff check --fix code/' to fix."

echo "Setup complete."
