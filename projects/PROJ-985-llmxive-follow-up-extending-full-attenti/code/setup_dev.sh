#!/bin/bash
# Setup script for development environment
# Installs dev dependencies and initializes pre-commit hooks

set -e

echo "Installing development dependencies..."
pip install -r requirements-dev.txt

echo "Initializing pre-commit hooks..."
pre-commit install

echo "Running initial lint check on existing code..."
pre-commit run --all-files || true

echo "Development environment setup complete!"
echo "To run linting manually: pre-commit run --all-files"
echo "To format code: black code/"
echo "To check linting: ruff check code/"