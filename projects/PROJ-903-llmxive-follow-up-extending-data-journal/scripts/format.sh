#!/bin/bash
set -e

echo "Running formatter (black)..."
python -m black code/ tests/

echo "Running linter auto-fix (ruff)..."
python -m ruff check --fix code/ tests/

echo "Formatting complete!"
