#!/bin/bash
# Setup script for linting and formatting tools
# Usage: bash setup_linting.sh

set -e

echo "Installing linting and formatting tools..."
pip install ruff black pytest

echo "Running initial ruff check..."
ruff check code/ tests/ || true

echo "Running initial black check (dry-run)..."
black --check code/ tests/ || true

echo "Setup complete. To auto-fix: ruff check --fix && black code/ tests/"
