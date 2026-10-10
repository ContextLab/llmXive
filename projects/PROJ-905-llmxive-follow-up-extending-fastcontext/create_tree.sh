#!/bin/bash
set -e

PROJECT_ROOT="projects/PROJ-905-llmxive-follow-up-extending-fastcontext"

# Create all directories
mkdir -p "$PROJECT_ROOT/data/raw"
mkdir -p "$PROJECT_ROOT/data/processed"
mkdir -p "$PROJECT_ROOT/data/results"
mkdir -p "$PROJECT_ROOT/code"
mkdir -p "$PROJECT_ROOT/tests/unit"
mkdir -p "$PROJECT_ROOT/tests/integration"
mkdir -p "$PROJECT_ROOT/specs/contracts"
mkdir -p "$PROJECT_ROOT/state"

# Generate tree output
mkdir -p "$PROJECT_ROOT/data/processed"
tree -L 3 "$PROJECT_ROOT" > "$PROJECT_ROOT/data/processed/dir_structure.txt" 2>/dev/null || find "$PROJECT_ROOT" -type d | head -20 > "$PROJECT_ROOT/data/processed/dir_structure.txt"

echo "Directory structure created successfully."
echo "Contents of dir_structure.txt:"
cat "$PROJECT_ROOT/data/processed/dir_structure.txt"