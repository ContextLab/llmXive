#!/bin/bash
set -e

echo "Running pre-commit checks (format + lint)..."

# Check formatting
black --check code/ tests/

# Check linting
ruff check code/ tests/

# Check with flake8 (optional compatibility layer)
flake8 code/ tests/

echo "All checks passed."
