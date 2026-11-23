#!/bin/bash
# Run both linting and formatting checks
set -e

echo "=== Running Linting ==="
bash scripts/lint.sh

echo "=== Running Formatting ==="
bash scripts/format.sh

echo "=== All checks passed ==="