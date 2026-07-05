#!/bin/bash
# Script to lint code using Ruff
# Usage: ./scripts/lint.sh

set -e

echo "Linting code with Ruff..."
ruff check code/ tests/
echo "Done."
