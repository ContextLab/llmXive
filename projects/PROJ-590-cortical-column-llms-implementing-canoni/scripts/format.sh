#!/bin/bash
# Run formatter and auto-fix linter issues
set -e

echo "Running Black formatter..."
black .

echo "Running Ruff fix..."
ruff check . --fix

echo "Formatting complete."