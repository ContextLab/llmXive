#!/bin/bash
set -e

echo "Running Ruff linter (strict mode)..."
ruff check src/ tests/ scripts/

echo "Running Black check (verify formatting)..."
black --check src/ tests/ scripts/

echo "Linting complete. No issues found."
