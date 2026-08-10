#!/bin/bash
# Formatting script for T003

set -e

echo "Running Black..."
black code/ tests/

echo "Running isort..."
isort code/ tests/

echo "Formatting complete!"
