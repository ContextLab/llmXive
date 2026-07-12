#!/bin/bash
# Script to format code according to project standards (Black + isort)

set -e

echo "Running isort..."
python -m isort code/ tests/

echo "Running black..."
python -m black --line-length 100 code/ tests/

echo "Formatting complete."
