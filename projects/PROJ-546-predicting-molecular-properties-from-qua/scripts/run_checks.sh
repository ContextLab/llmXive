#!/bin/bash
# Run all quality checks: linting and formatting
set -e

echo "=== Running Quality Checks ==="

echo "1. Running ruff check..."
ruff check code/ tests/

echo "2. Running black check (dry run)..."
black --check code/ tests/

echo "=== All checks passed ==="
