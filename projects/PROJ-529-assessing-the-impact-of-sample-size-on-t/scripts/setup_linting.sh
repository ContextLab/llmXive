#!/bin/bash
# Setup script for linting and formatting tools
# This script installs ruff and black and performs an initial check/format

set -e

echo "Installing linting and formatting tools..."
pip install ruff black

echo "Running initial ruff check..."
ruff check code/ tests/ || true

echo "Running initial black format check..."
black --check code/ tests/ || true

echo "Setup complete. Run 'ruff check . && black .' to fix issues."
