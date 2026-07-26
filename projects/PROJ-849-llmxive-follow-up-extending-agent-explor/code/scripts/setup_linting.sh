#!/bin/bash
# Setup script to initialize linting and formatting tools

set -e

echo "Installing development dependencies..."
pip install -r requirements-dev.txt

echo "Initializing pre-commit hooks..."
pre-commit install

echo "Running initial ruff check..."
ruff check .

echo "Running initial black format check..."
black --check .

echo "Setup complete. Run 'pre-commit run --all-files' to lint/format all files."