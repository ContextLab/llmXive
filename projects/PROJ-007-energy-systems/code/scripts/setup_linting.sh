#!/bin/bash
# Script to install and configure linting tools for PROJ-007-energy-systems

set -e

echo "Installing development dependencies..."
pip install -r requirements-dev.txt

echo "Installing pre-commit hooks..."
pre-commit install

echo "Running initial lint check..."
ruff check .
black --check .

echo "Linting and formatting tools configured successfully."
