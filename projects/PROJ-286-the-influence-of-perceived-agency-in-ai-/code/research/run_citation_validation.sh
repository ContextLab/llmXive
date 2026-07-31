#!/bin/bash
# Script to execute T000b: Validate specific citations and generate the report.
# This script ensures the Python module is executed with the correct arguments.

set -e

# Ensure we are in the project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

# Create the research directory if it doesn't exist
mkdir -p research

# Run the validation script
python code/research/validate_citations.py \
    --citations "Lee & See (2004), Langer (1975)" \
    --output research/validation_report.json

echo "Citation validation complete. Report saved to research/validation_report.json"
