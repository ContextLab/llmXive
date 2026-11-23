#!/bin/bash
# Script to generate API documentation for llmXive
# This script must be run from the project root directory

set -e

echo "Installing documentation dependencies..."
pip install -r docs/requirements-docs.txt

echo "Generating API documentation..."
cd docs
make html

echo "Documentation generated successfully at docs/_build/html/index.html"
echo "To view, open docs/_build/html/index.html in a browser."
