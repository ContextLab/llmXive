#!/bin/bash
# Format code with Black and Ruff
set -e
cd "$(dirname "$0")/.."
echo "Running Black..."
black code/
echo "Running Ruff fix..."
ruff check --fix code/
echo "Formatting complete."
