#!/bin/bash
# Script to initialize linting and formatting configuration for the project.
# This script assumes it is run from the project root or code/ directory.

set -e

echo "Installing linting and formatting tools..."
pip install ruff black

echo "Linting and formatting configuration files created:"
echo "  - .ruff.toml"
echo "  - .black.toml"
echo ""
echo "To run linter:"
echo "  ruff check ."
echo ""
echo "To run formatter:"
echo "  black ."
echo ""
echo "To run both (fix issues where possible):"
echo "  ruff check --fix ."
echo "  black ."
