#!/bin/bash
# Run formatting checks and apply fixes using black
set -e

echo "Running black format..."
black code/ tests/

echo "Formatting complete."
