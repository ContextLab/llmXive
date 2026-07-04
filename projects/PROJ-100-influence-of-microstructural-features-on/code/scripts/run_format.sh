#!/bin/bash
# Script to format code using Black
set -e
echo "Running Black formatter..."
black .
echo "Formatting complete."
