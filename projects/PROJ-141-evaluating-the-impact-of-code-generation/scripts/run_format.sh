#!/bin/bash
# Script to format code with black

set -e

echo "=== Running Code Formatting ==="
echo ""

# Check if black is installed
if ! command -v black &> /dev/null; then
    echo "ERROR: black is not installed. Run: pip install black"
    exit 1
fi

echo "Running black formatter..."
black code/ tests/

echo ""
echo "=== Formatting complete ==="
