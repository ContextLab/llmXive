#!/bin/bash
# Setup script to ensure data directories exist
# In a real scenario, this might download data or symlink from a shared location.

set -e

echo "Ensuring data directories..."
mkdir -p data/raw
mkdir -p data/processed

# Check for raw data
if [ ! -f "data/raw/trajectories.csv" ]; then
    echo "WARNING: data/raw/trajectories.csv not found."
    echo "Please ensure the raw trajectory data is placed in this directory."
    exit 1
fi

echo "Data structure ready."