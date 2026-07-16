#!/usr/bin/env bash
set -euo pipefail

echo "=== Running Quality Checks ==="

echo "1. Formatting check (black --check)..."
black --check code/ tests/ scripts/

echo "2. Import sorting check (isort --check)..."
isort --check code/ tests/ scripts/

echo "3. Linting check (flake8)..."
flake8 code/ tests/ scripts/

echo "=== All Quality Checks Passed ==="
