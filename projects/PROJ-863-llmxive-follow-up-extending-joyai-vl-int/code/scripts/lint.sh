#!/bin/bash
# Run linter checks without fixing
# Usage: ./scripts/lint.sh

set -e

echo "Running Ruff linter..."
ruff check code/ tests/

echo "Running Black check (dry run)..."
black --check code/ tests/

echo "Linting complete."
