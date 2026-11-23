#!/bin/bash
# Format code with Black and Ruff
set -e

echo "Running Black..."
black src/ tests/ --exclude "data/"

echo "Running Ruff fix..."
ruff check src/ tests/ --fix --exclude "data/"

echo "Formatting complete."
