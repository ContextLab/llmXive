#!/bin/bash
# Auto-format code with black
set -e

echo "Formatting code with black..."
black code/ tests/ --config=pyproject.toml

echo "Code formatted successfully."