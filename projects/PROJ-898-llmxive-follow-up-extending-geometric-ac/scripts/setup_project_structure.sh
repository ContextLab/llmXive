#!/bin/bash
# Script to set up the standard project directory structure for llmXive
# This script ensures code/, data/, tests/ and data subdirectories exist with .gitkeep files.

set -e

echo "Setting up project directory structure..."

# Create main directories
mkdir -p code
mkdir -p tests
mkdir -p data/raw
mkdir -p data/generated
mkdir -p data/results

# Create .gitkeep files to ensure directories are tracked by git
touch code/.gitkeep
touch tests/.gitkeep
touch data/.gitkeep
touch data/raw/.gitkeep
touch data/generated/.gitkeep
touch data/results/.gitkeep

echo "Directory structure created successfully:"
echo "  - code/"
echo "  - tests/"
echo "  - data/raw/"
echo "  - data/generated/"
echo "  - data/results/"

echo "Setup complete."