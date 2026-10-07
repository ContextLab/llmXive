#!/bin/bash
# Run formatters on the project
set -e

echo "Running Black formatter..."
black code/ tests/

echo "Running Ruff fix..."
ruff check --fix code/ tests/

echo "Formatting complete."
