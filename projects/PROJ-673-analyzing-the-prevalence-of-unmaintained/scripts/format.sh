#!/bin/bash
set -e

echo "Running formatter (black)..."
black code/ tests/

echo "Running linter auto-fix (ruff)..."
ruff check --fix code/ tests/

echo "Formatting and linting auto-fix complete."