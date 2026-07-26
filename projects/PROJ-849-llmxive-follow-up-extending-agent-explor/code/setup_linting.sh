#!/bin/bash
# Setup script for linting and formatting tools
# This script installs dev dependencies and initializes configuration

set -e

echo "Installing dev dependencies (ruff, black, pytest)..."
pip install -e ".[dev]"

echo "Verifying installation..."
python -m ruff --version
python -m black --version

echo "Running initial lint check (expecting clean or warnings only)..."
python -m ruff check code/ --output-format=full || true

echo "Linting and formatting configuration ready."
echo "To format code: python -m black code/"
echo "To lint code: python -m ruff check code/"