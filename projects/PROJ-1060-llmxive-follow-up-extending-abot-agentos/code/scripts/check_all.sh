#!/bin/bash
# Script to run both linting and formatting checks
# Usage: ./scripts/check_all.sh

set -e

echo "Running all code quality checks..."

echo "--- Running Ruff ---"
ruff check .

echo "--- Running Black (check mode) ---"
black --check .

echo "--- All checks passed ---"
