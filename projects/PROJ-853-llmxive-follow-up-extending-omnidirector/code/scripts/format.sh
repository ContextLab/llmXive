#!/bin/bash
# Format code with Black and sort imports with Ruff
set -e
echo "Formatting code with Black..."
black code/
echo "Linting and fixing with Ruff..."
ruff check --fix code/
echo "Formatting complete."
