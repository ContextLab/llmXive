#!/bin/bash
# Entry point script for PROJ-756
# Constitution Principle I: Project must be immediately runnable

set -e

echo "Starting PROJ-756 pipeline..."

# Ensure Python environment is active
if [ -z "$VIRTUAL_ENV" ]; then
    echo "Warning: No virtual environment detected. Proceeding with system Python."
fi

# Run the main pipeline
python code/main.py --full-pipeline

echo "Pipeline execution completed."