#!/bin/bash
set -e

echo "Running Black formatter..."
black code/ tests/

echo "Running Ruff linter (fix mode)..."
ruff check --fix code/ tests/

echo "Running Ruff linter (report only)..."
ruff check code/ tests/

echo "Formatting and linting complete."
