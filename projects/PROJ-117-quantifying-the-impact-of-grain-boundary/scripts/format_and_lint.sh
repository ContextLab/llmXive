#!/bin/bash
set -e

echo "Formatting code..."
black code/ tests/
ruff check code/ tests/ --fix

echo "Linting code..."
ruff check code/ tests/
black --check code/ tests/

echo "All checks passed."
