#!/bin/bash
# Script to automatically format code
# Task: T003 - Configure linting (ruff) and formatting (black)

set -e

echo "Running Black Formatting..."
black code/ tests/

echo "Running Ruff Fix..."
ruff check --fix code/ tests/

echo "Formatting complete!"