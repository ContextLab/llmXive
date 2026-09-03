#!/bin/bash
# Format code with Black and sort imports with Ruff
set -e
echo "Formatting code with Black..."
black code/ tests/
echo "Sorting imports with Ruff..."
ruff check --fix code/ tests/
echo "Formatting complete."
