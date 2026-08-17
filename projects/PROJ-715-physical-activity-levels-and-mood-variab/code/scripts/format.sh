#!/bin/bash
# Script to run black formatting on the codebase

set -e

echo "Running black formatting..."
black code/

if [ $? -eq 0 ]; then
    echo "Formatting completed!"
    exit 0
else
    echo "Formatting failed!"
    exit 1
fi
