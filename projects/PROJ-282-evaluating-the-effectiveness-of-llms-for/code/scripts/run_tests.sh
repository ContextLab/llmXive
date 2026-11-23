#!/bin/bash
set -e
echo "Running tests with pytest..."
cd "$(dirname "$0")/.."
pytest code/tests -v
echo "Tests complete."