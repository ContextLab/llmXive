#!/bin/bash
set -e

echo "Running Ruff linter..."
ruff check code/ src/ tests/

echo "Running Flake8 linter..."
flake8 code/ src/ tests/ --max-line-length=88 --ignore=E203,W503

echo "Linting complete."