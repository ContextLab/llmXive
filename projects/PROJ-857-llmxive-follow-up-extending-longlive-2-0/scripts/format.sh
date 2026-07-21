#!/bin/bash
# Format code with Black and isort
set -e

echo "Running isort..."
isort code/ tests/

echo "Running Black..."
black code/ tests/

echo "Formatting complete."
