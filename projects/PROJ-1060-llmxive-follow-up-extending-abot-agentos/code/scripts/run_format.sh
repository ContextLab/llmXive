#!/bin/bash
# Script to run Black formatting on the codebase
# Usage: ./scripts/run_format.sh

set -e

echo "Running Black formatting..."
black .

echo "Formatting complete."
