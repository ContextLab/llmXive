#!/bin/bash
# Script to generate API documentation for llmXive

set -e

echo "Building llmXive API documentation..."

# Create source directory if it doesn't exist
mkdir -p docs/source

# Change to docs directory
cd docs

# Install dependencies if needed
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Clean old build
rm -rf _build

# Generate documentation
echo "Generating documentation..."
sphinx-apidoc -o source ../code -f -M -e -d 4

# Build HTML
echo "Building HTML output..."
make html

echo "Documentation built successfully!"
echo "Open docs/_build/html/index.html in your browser to view."

# Deactivate virtual environment
deactivate
