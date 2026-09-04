#!/bin/bash
# Script to run only linting checks (no auto-fix)
# Usage: ./scripts/lint_check.sh

set -e

echo "Running linting checks..."

# Run Ruff (includes flake8, pyflakes, isort, etc.)
ruff check code/ tests/

# Run Black check (syntax/style)
black --check code/ tests/

echo "Linting checks complete."
