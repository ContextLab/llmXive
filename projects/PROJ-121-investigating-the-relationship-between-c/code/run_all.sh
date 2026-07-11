#!/bin/bash
set -e

echo "Starting full pipeline execution..."

# Ensure directories exist
python code/scripts/setup_directories.py

# Run the main pipeline
python code/src/pipeline.py --bin-size 27

echo "Data acquisition completed"
