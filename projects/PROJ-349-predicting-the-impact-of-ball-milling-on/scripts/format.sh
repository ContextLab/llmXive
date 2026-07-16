#!/bin/bash
set -e

echo "Running isort..."
isort src/ tests/

echo "Running black..."
black src/ tests/

echo "Formatting complete."
