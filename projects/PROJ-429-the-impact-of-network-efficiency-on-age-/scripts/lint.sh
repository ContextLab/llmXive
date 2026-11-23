#!/bin/bash
set -e

echo "Running linter (ruff)..."
ruff check code/ tests/

echo "Running linter (flake8)..."
flake8 code/ tests/

echo "Linting complete."
