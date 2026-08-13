#!/bin/bash
# Script to run linting and formatting checks as per task T031b.
# This script executes `ruff check` and `black --check` on the src/ directory.
# It exits with code 0 only if both tools report no issues.

set -e

echo "Running Ruff check on src/..."
ruff check code/src/

echo "Running Black check on src/..."
black --check code/src/

echo "Linting checks passed successfully."
exit 0