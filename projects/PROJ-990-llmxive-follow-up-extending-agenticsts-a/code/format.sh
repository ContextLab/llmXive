#!/bin/bash
# Run Black and Ruff formatter on code/ and tests/
# This script ensures consistent formatting across the project.

set -e

echo "Running Black formatter..."
black code/ tests/

echo "Running Ruff formatter..."
ruff format code/ tests/

echo "Formatting complete."
