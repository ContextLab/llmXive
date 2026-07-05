#!/bin/bash
# Format code using black

set -e

echo "Running black formatting..."
black code/ tests/

echo "Formatting complete."
