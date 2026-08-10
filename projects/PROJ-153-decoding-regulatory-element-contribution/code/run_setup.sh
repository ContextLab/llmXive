#!/bin/bash
# Run the project structure setup script
# This ensures all required directories exist before pipeline execution

set -e

echo "Running project setup..."
python code/setup_project_structure.py

echo "Setup verification:"
if [ -d "code" ] && [ -d "tests" ] && [ -d "data" ] && [ -d "results" ]; then
    echo "✓ All primary directories created successfully."
else
    echo "✗ Failed to create required directories."
    exit 1
fi
