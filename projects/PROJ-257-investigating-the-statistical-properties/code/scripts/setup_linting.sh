#!/bin/bash
# Setup script for linting and formatting tools
# This script installs pre-commit hooks and validates the environment

set -e

echo "Installing development dependencies..."
pip install -r requirements-dev.txt

echo "Initializing pre-commit hooks..."
pre-commit install

echo "Running initial lint check on existing files..."
# Run ruff on existing code to ensure baseline compliance
ruff check code/ || true
black --check code/ || true

echo "Setup complete. Run 'pre-commit run --all-files' to check all files."