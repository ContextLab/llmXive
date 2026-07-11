#!/bin/bash
set -e

echo "Running Black Formatter..."
black code/ tests/

echo "Running Ruff Auto-fix..."
ruff check --fix code/ tests/

echo "Formatting complete."