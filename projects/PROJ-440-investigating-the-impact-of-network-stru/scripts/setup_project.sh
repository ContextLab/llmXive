#!/bin/bash
# Script to initialize the project directory structure
# Run from the project root directory

set -e

echo "Setting up project directory structure..."

# Create directories
mkdir -p code data/raw data/processed data/analysis tests contracts state

echo "Directory structure created successfully."
echo ""
echo "Created directories:"
echo "  - code/"
echo "  - data/"
echo "    - raw/"
echo "    - processed/"
echo "    - analysis/"
echo "  - tests/"
echo "  - contracts/"
echo "  - state/"