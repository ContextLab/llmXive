#!/bin/bash
# Format code with black and isort
set -e

echo "Running isort..."
python -m isort code/ tests/

echo "Running black..."
python -m black code/ tests/

echo "Formatting complete."
