#!/bin/bash
# Run linter and formatter checks
set -e

echo "Running Ruff lint..."
ruff check .

echo "Running Black check..."
black --check .

echo "All checks passed."
