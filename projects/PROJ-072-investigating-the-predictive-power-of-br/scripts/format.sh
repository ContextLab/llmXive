#!/bin/bash
set -e

echo "Running formatter (black)..."
black code/ tests/

echo "Running linter (ruff)..."
ruff check code/ tests/

echo "Formatting and linting complete."
