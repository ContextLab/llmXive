#!/bin/bash
# Script to format the codebase using Black and sort imports with isort.

set -e

echo "Formatting code with Black..."
black code/ tests/

echo "Sorting imports with isort..."
isort code/ tests/

echo "Code formatting complete."
