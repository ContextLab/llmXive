#!/bin/bash
# Setup script for linting and formatting tools
# Run this after installing requirements.txt

set -e

echo "Installing pre-commit hooks..."
pre-commit install

echo "Running initial lint check on existing code..."
flake8 code/ --max-line-length=88 --extend-ignore=E203,W503 --exclude=__pycache__,build,dist

echo "Formatting code with Black..."
black code/ tests/ --line-length=88

echo "Sorting imports with isort..."
isort code/ tests/ --profile=black --line-length=88

echo "Linting and formatting setup complete!"
echo "To run manually:"
echo "  pre-commit run --all-files"
echo "  black code/ tests/"
echo "  flake8 code/ tests/"