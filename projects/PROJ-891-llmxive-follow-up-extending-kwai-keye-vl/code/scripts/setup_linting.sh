#!/bin/bash
set -e

echo "Installing linting and formatting tools..."
pip install -e ".[dev]"

echo "Linting and formatting configuration files created."
echo "Run 'ruff check .' to check for issues."
echo "Run 'black .' to format code."
echo "Run 'ruff check --fix .' to auto-fix issues."
