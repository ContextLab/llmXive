#!/bin/bash
# Format code with black and isort
set -e
echo "Running isort..."
isort code/
echo "Running black..."
black code/
echo "Formatting complete."