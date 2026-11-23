#!/bin/bash
# Script to set up the data directory structure and .gitkeep files
# This script runs the Python implementation to ensure consistency

set -e

echo "Setting up data directory structure..."
python code/setup_data_dirs.py

echo "Verifying data directories..."
if [ -d "data/raw" ] && [ -f "data/raw/.gitkeep" ] && \
   [ -d "data/generated" ] && [ -f "data/generated/.gitkeep" ] && \
   [ -d "data/results" ] && [ -f "data/results/.gitkeep" ]; then
    echo "Data directory structure verified successfully."
else
    echo "ERROR: Data directory structure verification failed."
    exit 1
fi

echo "Setup complete."
