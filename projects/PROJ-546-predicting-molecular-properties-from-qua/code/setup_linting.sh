#!/bin/bash
# Setup script to install linting and formatting tools and run initial checks
# Usage: bash code/setup_linting.sh

set -e

echo "Installing linting and formatting tools..."
pip install ruff black pytest

echo "Running initial Ruff check..."
# Run ruff on the code directory
ruff check code/ || {
    echo "Ruff found issues. Please fix them before proceeding."
    exit 1
}

echo "Running initial Black check..."
# Run black in check mode
black --check code/ || {
    echo "Black found formatting issues. Run 'black code/' to fix."
    exit 1
}

echo "Linting and formatting setup complete. All checks passed."