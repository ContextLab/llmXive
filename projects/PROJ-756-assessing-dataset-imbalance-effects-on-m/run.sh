#!/bin/bash
# Entry point script for PROJ-756
# Ensures the project is immediately runnable per Constitution Principle I

set -e

echo "Initializing PROJ-756 pipeline..."

# Ensure directories exist
mkdir -p data/raw data/processed artifacts results state logs logs/archive

# Run the main pipeline
python code/main.py --full-pipeline --streaming

echo "Pipeline execution completed."
