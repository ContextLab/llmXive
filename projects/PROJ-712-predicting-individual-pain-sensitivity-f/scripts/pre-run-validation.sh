#!/bin/bash
# Pre-run validation script for llmXive project PROJ-712.
# Ensures that all required citations are present in CITATIONS.bib
# before the pipeline runs. Exits non-zero if any citation is missing.

set -e

# Resolve the project root relative to this script's directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "=== Pre-run Validation ==="
echo "Project Root: $PROJECT_ROOT"

# Invoke the citation validation logic in code/utils.py.
# The python command exits with 0 if all citations are present,
# and 1 if any are missing, satisfying the task requirement.
python -m code.utils --validate-citations

echo "Pre-run validation passed."