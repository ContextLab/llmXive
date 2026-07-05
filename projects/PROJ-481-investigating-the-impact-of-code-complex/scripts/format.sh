#!/bin/bash
# Script to format code using Black
# Usage: ./scripts/format.sh

set -e

echo "Formatting code with Black..."
black code/ tests/
echo "Done."
