#!/bin/bash
# Format code with Black and Ruff
set -e
echo "Running Black..."
black code/ tests/
echo "Running Ruff Fix..."
ruff check --fix code/ tests/
echo "Formatting complete."
