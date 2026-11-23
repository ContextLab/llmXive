#!/bin/bash
# Script to automatically format code
# Usage: ./scripts/format.sh

set -e

echo "Running Black Formatter..."
black code/ tests/

echo "Running Ruff Fix..."
ruff check --fix code/ tests/

echo "Formatting complete."
