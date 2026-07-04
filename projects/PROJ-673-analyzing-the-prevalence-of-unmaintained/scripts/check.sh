#!/bin/bash
# Run both linting and formatting checks
set -e

echo "Running lint checks..."
ruff check .

echo "Running format checks (dry-run)..."
black --check .

echo "All checks passed."