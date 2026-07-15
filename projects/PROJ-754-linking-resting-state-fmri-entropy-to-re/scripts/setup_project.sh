#!/bin/bash
# Setup script for llmXive project structure

set -e

echo "Creating project directory structure..."

# Create main directories
mkdir -p code/config
mkdir -p code/data
mkdir -p code/analysis
mkdir -p code/stats
mkdir -p tests/unit
mkdir -p tests/integration
mkdir -p data/raw
mkdir -p data/cleaned
mkdir -p data/derived
mkdir -p data/results
mkdir -p figures
mkdir -p reports
mkdir -p specs/001-linking-resting-state-fmri-entropy-to-re

# Create empty __init__.py files
touch code/config/__init__.py
touch code/data/__init__.py
touch code/analysis/__init__.py
touch code/stats/__init__.py
touch tests/__init__.py
touch tests/unit/__init__.py
touch tests/integration/__init__.py
touch specs/001-linking-resting-state-fmri-entropy-to-re/__init__.py

# Create checksums file
touch data/checksums.txt

echo "Project structure created successfully!"
echo "Next steps:"
echo "  1. pip install -r requirements.txt"
echo "  2. Set HCP_TOKEN environment variable"
echo "  3. Run python -m pytest to verify setup"
