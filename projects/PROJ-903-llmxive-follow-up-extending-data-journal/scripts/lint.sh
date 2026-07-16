#!/bin/bash
set -e

echo "Running linter (ruff)..."
python -m ruff check code/ tests/

echo "Running formatter check (black)..."
python -m black --check code/ tests/

echo "All checks passed!"
