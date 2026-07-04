#!/bin/bash
# Format code with black and isort
set -e
echo "Running isort..."
python -m isort .
echo "Running black..."
python -m black .
echo "Formatting complete."
