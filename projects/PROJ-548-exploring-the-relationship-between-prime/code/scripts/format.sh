#!/usr/bin/env bash
set -euo pipefail

echo "Running Black formatter..."
black code/ tests/

echo "Running Ruff linter..."
ruff check code/ tests/

echo "Running Ruff autofix..."
ruff check --fix code/ tests/

echo "Formatting and linting complete."
