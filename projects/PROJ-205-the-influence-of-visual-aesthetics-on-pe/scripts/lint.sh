#!/bin/bash
# Run Ruff in strict mode (no autofix) to check for issues.
# Usage: ./scripts/lint.sh

set -e

echo "Running linter (Ruff)..."
python -m ruff check code/ tests/

echo "Running formatter check (Black)..."
python -m black --check code/ tests/

echo "Linting complete."