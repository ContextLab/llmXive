#!/bin/bash
# Script to check if code is formatted correctly (without modifying)

set -e

echo "Checking formatting..."
black --check code/

if [ $? -eq 0 ]; then
    echo "Code is properly formatted!"
    exit 0
else
    echo "Code needs formatting. Run 'bash code/scripts/format.sh' to fix."
    exit 1
fi
