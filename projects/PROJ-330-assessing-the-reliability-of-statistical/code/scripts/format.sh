#!/bin/bash
# Formatting script for the project
# Runs black and isort to format code

set -e

echo "Running formatter (black)..."
python -m black --line-length 88 code/src code/scripts code/tests

echo "Running import sorter (isort)..."
python -m isort --profile black --line-length 88 code/src code/scripts code/tests

echo "Code formatted successfully!"