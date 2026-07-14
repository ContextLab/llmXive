#!/bin/bash
# Setup script for linting and formatting tools
# Installs ruff and black, then runs initial formatting and linting checks

set -e

echo "Installing linting and formatting tools..."
pip install ruff black

echo "Formatting code with Black..."
black code/ tests/

echo "Linting code with Ruff..."
ruff check code/ tests/

echo "Linting complete. Run 'ruff check --fix' to automatically fix issues."
echo "Run 'black --check code/ tests/' to verify formatting compliance."
