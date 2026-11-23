#!/bin/bash
# Script to format code using Black
# Usage: ./scripts/format_code.sh

set -e

echo "Formatting code with Black..."
black code/
echo "Code formatting complete."
