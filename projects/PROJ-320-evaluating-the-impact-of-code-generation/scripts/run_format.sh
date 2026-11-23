#!/bin/bash
# Script to run black formatting on the project

set -e

echo "Running black formatting..."
black code/ tests/

echo "Formatting completed successfully!"
