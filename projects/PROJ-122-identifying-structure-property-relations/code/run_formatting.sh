#!/bin/bash
# Apply Black formatting to the project

set -e

echo "Running Black formatter..."
black --line-length 100 code/

echo "Formatting applied successfully."