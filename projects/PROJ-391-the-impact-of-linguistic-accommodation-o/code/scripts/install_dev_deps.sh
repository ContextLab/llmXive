#!/bin/bash
# Install development dependencies
set -e

echo "Installing development dependencies..."
if [ -f "requirements-dev.txt" ]; then
    pip install -r requirements-dev.txt
    echo "Development dependencies installed successfully."
else
    echo "Error: requirements-dev.txt not found."
    exit 1
fi
