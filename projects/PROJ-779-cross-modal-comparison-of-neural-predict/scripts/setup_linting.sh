#!/bin/bash
# Script to initialize linting and formatting tools for the project.
# This script assumes a virtual environment is already activated.

set -e

echo "Installing development dependencies (black, ruff, pre-commit)..."
pip install black ruff pre-commit

echo "Initializing pre-commit hooks..."
pre-commit install

echo "Running initial format check (dry-run)..."
black --check . || true

echo "Running initial lint check (dry-run)..."
ruff check . || true

echo "Setup complete. Run 'pre-commit run --all-files' to manually check all files."
