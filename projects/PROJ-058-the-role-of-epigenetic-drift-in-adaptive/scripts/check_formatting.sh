#!/bin/bash
# Script to check and fix formatting/linting for PROJ-058

set -e

echo "Running Black formatting check..."
black --check code/ tests/ || (
    echo "Formatting issues found. Running Black to fix..."
    black code/ tests/
)

echo "Running Ruff linting check..."
ruff check code/ tests/ || (
    echo "Linting issues found. Attempting auto-fix..."
    ruff check --fix code/ tests/
)

echo "All checks passed."
