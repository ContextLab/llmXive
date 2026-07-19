#!/bin/bash
set -e

echo "Running Ruff linter..."
ruff check code/ tests/

echo "Running Ruff formatter check (dry-run)..."
ruff format --check code/ tests/

echo "Linting complete."
