#!/bin/bash
# Script to ensure data directories exist before running the pipeline
# This is a safeguard for the run-book

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "Ensuring data directories exist in: $PROJECT_ROOT"

python3 -c "
import sys
sys.path.insert(0, '$PROJECT_ROOT/code')
from setup_directories import setup_directories
if not setup_directories():
    sys.exit(1)
"

echo "Data directories verified."