#!/bin/bash
set -e

echo "Formatting code..."

# Format Python files
black code/ tests/
isort code/ tests/

echo "Formatting complete."
