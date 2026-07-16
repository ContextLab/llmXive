#!/usr/bin/env bash
# Script to check formatting and linting without modifying files.
# Used in CI/CD pipelines.

set -e

echo "Checking formatter (black)..."
black --check code/

echo "Checking linter (ruff)..."
ruff check code/

echo "All checks passed."
exit 0