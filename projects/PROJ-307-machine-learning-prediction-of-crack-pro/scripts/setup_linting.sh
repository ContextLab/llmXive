#!/bin/bash
# Setup script to install linting and formatting tools and run initial checks
# This script is idempotent.

set -e

echo "Installing development dependencies..."
pip install -e ".[dev]"

echo "Running Black check (dry run)..."
black --check code/ tests/ || (echo "Black formatting issues found. Run 'black code/ tests/' to fix." && exit 1)

echo "Running Ruff check..."
ruff check code/ tests/ || (echo "Ruff linting issues found. Run 'ruff check --fix code/ tests/' to fix." && exit 1)

echo "Linting and formatting setup complete and verified."