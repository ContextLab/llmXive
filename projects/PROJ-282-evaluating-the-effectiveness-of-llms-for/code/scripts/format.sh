#!/bin/bash
# Script to format code using black
# Exit on error
set -e

echo "Running Black formatter..."
black code/

echo "Formatting complete."
