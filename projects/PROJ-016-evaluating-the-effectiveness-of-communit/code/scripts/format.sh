#!/bin/bash
# Run ruff fix and black formatter
set -e

echo "Running ruff fix..."
ruff check --fix code/

echo "Running black formatter..."
black code/

echo "Formatting complete."
