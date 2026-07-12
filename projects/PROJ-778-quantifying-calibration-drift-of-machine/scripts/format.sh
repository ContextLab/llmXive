#!/usr/bin/env bash
set -e

echo "Running Black formatter..."
black code/ tests/

echo "Running Ruff linter (fix mode)..."
ruff check code/ tests/ --fix

echo "Running Ruff linter (strict mode, no fix)..."
ruff check code/ tests/

echo "Formatting and linting complete."
