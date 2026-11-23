#!/usr/bin/env bash
set -euo pipefail

echo "Formatting code with black..."
black code/

echo "Fixing linting issues with ruff..."
ruff check --fix code/

echo "Formatting complete."
