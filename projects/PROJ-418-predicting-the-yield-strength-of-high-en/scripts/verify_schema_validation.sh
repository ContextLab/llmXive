#!/bin/bash
# Script to verify T121: Run schema validation tests and report results.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "Running T121 Schema Validation Verification..."

cd "$PROJECT_ROOT"

# Run the specific test file
python -m pytest tests/unit/test_schema_validation.py -v --tb=short

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo "T121 Verification: SUCCESS"
    echo "All schema validations (T098-T101) passed."
else
    echo "T121 Verification: FAILED"
    echo "One or more schema validations failed."
fi

exit $EXIT_CODE