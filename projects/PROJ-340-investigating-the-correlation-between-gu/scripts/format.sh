#!/usr/bin/env bash
set -euo pipefail

echo "Running code formatter (black)..."
black code/ tests/ scripts/

echo "Running import sorter (isort)..."
isort code/ tests/ scripts/

echo "Formatting complete."
