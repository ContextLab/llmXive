#!/bin/bash
set -e

# Project: PROJ-727 Assessing Energy Consumption of LLM Inference
# This script initializes the environment and runs the pipeline.

echo "Starting LLM Energy Assessment Pipeline..."

# Verify Python version
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3.10+ is required but not found."
    exit 1
fi

python_version=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
if [ "$(echo $python_version | cut -d. -f1)" -lt 3 ] || ([ "$(echo $python_version | cut -d. -f1)" -eq 3 ] && [ "$(echo $python_version | cut -d. -f2)" -lt 10 ]); then
    echo "Error: Python 3.10+ is required. Found: $python_version"
    exit 1
fi

echo "Python version check passed: $python_version"

# Install dependencies if not already installed
if ! python3 -c "import transformers" &> /dev/null; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
fi

# Create necessary directories if they don't exist
mkdir -p data/raw data/processed results/figures results/reports

# Run the main pipeline
echo "Running pipeline..."
python src/main.py

echo "Pipeline completed successfully."