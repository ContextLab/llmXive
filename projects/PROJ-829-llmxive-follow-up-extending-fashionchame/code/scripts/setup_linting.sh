#!/bin/bash
# Setup script for linting and formatting tools
# Run this after installing dependencies with: pip install -e ".[dev]"

set -e

echo "Installing development dependencies..."
pip install -e ".[dev]"

echo "Verifying ruff installation..."
ruff --version

echo "Verifying black installation..."
black --version

echo "Running initial lint check on code/src..."
ruff check code/src/ || echo "Lint warnings/errors found (expected on first run)"

echo "Running initial format check on code/src..."
black --check code/src/ || echo "Formatting issues found (expected on first run)"

echo "Setup complete. Run 'ruff check . && black .' to fix issues."