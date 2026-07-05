#!/bin/bash
# Setup linting and formatting tools for the project
# This script installs ruff and black if not already present

set -e

echo "Installing linting and formatting tools..."

# Install ruff (linter) and black (formatter)
pip install ruff black

# Verify installation
ruff --version
black --version

echo "Linting and formatting tools installed successfully."
echo ""
echo "Usage:"
echo "  Format code:     black code/ tests/"
echo "  Check format:    black --check code/ tests/"
echo "  Lint code:       ruff check code/ tests/"
echo "  Fix lint errors: ruff check --fix code/ tests/"
echo ""
echo "To run both in CI:"
echo "  black --check code/ tests/ && ruff check code/ tests/"
