#!/bin/bash
set -e

echo "Running formatters..."

# Run black
echo "Formatting with black..."
python -m black code/

# Run isort
echo "Sorting imports with isort..."
python -m isort code/

echo "All formatters completed."