#!/bin/bash
# Setup script for linting and formatting tools
# Usage: bash scripts/setup_linting.sh

set -e

echo "Installing linting and formatting tools..."

# Install tools via pip (should already be in requirements.txt)
pip install ruff black pre-commit

# Install pre-commit hooks
echo "Installing pre-commit hooks..."
pre-commit install

# Run initial check on all files
echo "Running initial linting check..."
pre-commit run --all-files || true

echo "Setup complete! To run manually:"
echo "  pre-commit run --all-files  # Check all files"
echo "  pre-commit run              # Check staged files only"
echo "  black code/ tests/          # Format code"
echo "  ruff check code/ tests/     # Lint code"
