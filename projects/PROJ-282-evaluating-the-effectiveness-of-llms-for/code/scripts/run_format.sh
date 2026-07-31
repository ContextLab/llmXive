#!/bin/bash
set -e
echo "Running formatting with black and ruff..."
cd "$(dirname "$0")/.."
black code/src code/tests code/setup_project_structure.py
ruff format code/src code/tests code/setup_project_structure.py
echo "Formatting complete."
