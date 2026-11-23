#!/bin/bash
set -e
echo "Running Black formatter..."
black code/
echo "Running Ruff (fixes)..."
ruff check --fix code/ || true
echo "Formatting complete."
