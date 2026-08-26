#!/bin/bash
set -e

echo "Running formatter (black)..."
python -m black .

echo "Running import sorter (isort)..."
python -m isort .

echo "Formatting complete."
