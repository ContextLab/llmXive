#!/bin/bash
# Format code using isort and black
# Usage: bash code/scripts/format_code.sh

set -e

echo "Running isort to organize imports..."
isort code/

echo "Running black to format code..."
black code/

echo "Code formatting complete!"
