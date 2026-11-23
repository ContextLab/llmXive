#!/bin/bash
set -e

echo "Formatting codebase..."

# Apply black formatting
black code/ tests/

# Apply isort
isort --profile black code/ tests/

echo "Formatting complete!"
