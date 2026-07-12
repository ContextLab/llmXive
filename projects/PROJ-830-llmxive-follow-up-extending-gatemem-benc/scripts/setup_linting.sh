#!/bin/bash
# Script to install and verify linting/formatting tools for GateMem project

set -e

echo "Installing dev dependencies..."
pip install -r requirements-dev.txt

echo "Verifying ruff installation..."
ruff --version

echo "Verifying black installation..."
black --version

echo "Running initial format check (dry-run)..."
black --check --diff code/ || true

echo "Running initial lint check..."
ruff check code/ || true

echo "Linting and formatting tools configured successfully."
echo "To format code: black code/"
echo "To lint code: ruff check code/"