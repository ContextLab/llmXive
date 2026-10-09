#!/bin/bash
# Pre-run validation script for llmXive project PROJ-712
# Implements Constitution Principle II: Verified Accuracy
# Checks for required citations before pipeline execution

set -e

# Determine project root (assuming script is in scripts/)
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "=== Pre-run Validation ==="
echo "Project Root: $PROJECT_ROOT"

# Validate citations using the utils module
echo "Checking citations..."
python -m code.utils --validate-citations

if [ $? -eq 0 ]; then
    echo "Validation successful. All checks passed."
else
    echo "Validation failed. Aborting pipeline execution."
    exit 1
fi
