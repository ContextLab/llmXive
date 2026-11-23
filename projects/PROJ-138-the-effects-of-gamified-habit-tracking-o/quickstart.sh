#!/bin/bash
set -e

echo "Starting Quickstart Validation..."

# Ensure we are in the project root
if [ ! -f "tasks.md" ]; then
    echo "Error: quickstart.sh must be run from the project root."
    exit 1
fi

# Install dependencies if requirements.txt exists
if [ -f "code/requirements.txt" ]; then
    echo "Installing dependencies..."
    pip install -r code/requirements.txt
fi

# Run the validation script
echo "Running validation script..."
python code/scripts/run_quickstart_validation.py

echo "Quickstart validation complete."
