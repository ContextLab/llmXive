#!/bin/bash
# Setup script for linting and formatting tools
# This script installs development dependencies and initializes configuration

set -e

echo "Installing development dependencies..."
pip install -r requirements-dev.txt

echo "Running initial ruff check..."
ruff check .

echo "Running initial black format check..."
black --check .

echo "Linting and formatting setup complete!"
echo "To format code: black ."
echo "To lint code: ruff check ."
echo "To fix lint errors automatically: ruff check --fix ."
