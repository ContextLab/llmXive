#!/bin/bash
# setup.sh - Creates the project directory structure
# Based on scripts/setup_manifest.txt

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "Setting up project directory structure in: $PROJECT_ROOT"

# Define directories to create relative to project root
DIRS=(
    "src/cli"
    "src/config"
    "src/evaluate"
    "src/ingest"
    "src/interpret"
    "src/model"
    "src/preprocess"
    "src/utils"
    "tests/contract"
    "tests/integration"
    "tests/unit"
    "data/raw"
    "data/processed"
    "data/splits"
    "results"
    "contracts"
    ".github/workflows"
    "scripts"
    "docs"
)

for dir in "${DIRS[@]}"; do
    full_path="$PROJECT_ROOT/$dir"
    if [ ! -d "$full_path" ]; then
        mkdir -p "$full_path"
        echo "Created: $full_path"
    else
        echo "Exists: $full_path"
    fi
done

# Create placeholder __init__.py files for Python packages
for pkg in src src/cli src/config src/evaluate src/ingest src/interpret src/model src/preprocess src/utils tests tests/contract tests/integration tests/unit; do
    touch "$PROJECT_ROOT/$pkg/__init__.py"
done

echo "Directory structure setup complete."