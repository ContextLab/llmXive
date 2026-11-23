#!/bin/bash
set -e

echo "Running Ruff linter (no auto-fix)..."
ruff check code/ tests/

echo "Linting complete."
