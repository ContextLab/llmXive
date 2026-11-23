#!/bin/bash
# Format code with Black and sort imports with ruff
set -e

echo "Running Black formatter..."
black code/

echo "Running ruff fixer..."
ruff check --fix code/

echo "Formatting complete."
