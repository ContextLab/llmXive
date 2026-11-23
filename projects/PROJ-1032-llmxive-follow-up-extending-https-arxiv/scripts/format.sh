#!/bin/bash
set -e

echo "Running Black formatter..."
black code/ tests/

echo "Running Ruff linter (auto-fix enabled)..."
ruff check code/ tests/ --fix

echo "Formatting and linting complete."
