#!/bin/bash
set -e

echo "Running linter (flake8)..."
python -m flake8 .

echo "Running formatter check (black)..."
python -m black --check .

echo "Running import sorter check (isort)..."
python -m isort --check-only .

echo "All checks passed."
