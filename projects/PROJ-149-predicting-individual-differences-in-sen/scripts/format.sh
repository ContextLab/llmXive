#!/bin/bash
set -e

echo "Formatting with black..."
black code/ tests/

echo "Sorting imports with isort..."
isort code/ tests/

echo "Formatting complete."