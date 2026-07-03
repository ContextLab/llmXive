#!/bin/bash
# Automatically format code with black and isort
# Exits with non-zero status if formatting fails

set -e

echo "Running isort..."
isort src/ tests/

echo "Running black..."
black src/ tests/

echo "Code formatted successfully."