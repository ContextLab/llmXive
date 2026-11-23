#!/bin/bash
# Script to automatically format code with Black and sort imports with Ruff
# Usage: ./scripts/format_code.sh

set -e

echo "Formatting code with Black..."
black code/

echo "Sorting imports with Ruff..."
ruff check --fix code/

echo "Code formatted successfully."
