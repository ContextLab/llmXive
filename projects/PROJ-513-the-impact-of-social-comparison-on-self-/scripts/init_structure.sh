#!/bin/bash
# Script to initialize the directory structure for the llmXive project
# Creates directories for stimuli, raw data, processed data, and pretest results

set -e

# Define the base directories to create
DIRS=(
    "data/stimuli/ai"
    "data/stimuli/human"
    "data/raw"
    "data/processed"
    "data/pretest"
)

# Create each directory if it doesn't exist
for dir in "${DIRS[@]}"; do
    if [ ! -d "$dir" ]; then
        mkdir -p "$dir"
        echo "Created directory: $dir"
    else
        echo "Directory already exists: $dir"
    fi
done

echo "Directory structure initialization complete."