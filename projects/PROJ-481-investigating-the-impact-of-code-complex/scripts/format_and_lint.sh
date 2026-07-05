#!/bin/bash
# Script to format and lint code
# Usage: ./scripts/format_and_lint.sh

set -e

echo "Running formatting and linting..."
./scripts/format.sh
./scripts/lint.sh
echo "All checks passed."