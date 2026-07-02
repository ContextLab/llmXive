#!/bin/bash
# Run Black and Ruff to format and lint the codebase.
# Usage: ./scripts/format.sh

set -e

echo "Formatting code with Black..."
python -m black code/ tests/

echo "Checking/fixing imports and style with Ruff..."
python -m ruff check --fix code/ tests/

echo "Done."
