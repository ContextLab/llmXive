#!/bin/bash
# Formatting script using Black
set -e
echo "Running Black formatter..."
black code/ tests/
echo "Formatting complete."
