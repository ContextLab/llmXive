#!/bin/bash
set -e

echo "Running code formatter (black)..."
black code/ src/ tests/

echo "Running linter (ruff)..."
ruff check code/ src/ tests/ --fix

echo "Formatting and linting complete."
