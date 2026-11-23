#!/bin/bash
set -e

PROJECT_ROOT="projects/PROJ-905-llmxive-follow-up-extending-fastcontext"

# Create all required directories
mkdir -p "$PROJECT_ROOT/data/raw"
mkdir -p "$PROJECT_ROOT/data/processed"
mkdir -p "$PROJECT_ROOT/data/results"
mkdir -p "$PROJECT_ROOT/code"
mkdir -p "$PROJECT_ROOT/tests/unit"
mkdir -p "$PROJECT_ROOT/tests/integration"
mkdir -p "$PROJECT_ROOT/specs/contracts"
mkdir -p "$PROJECT_ROOT/state"

# Verify all directories exist
for dir in "data/raw" "data/processed" "data/results" "code" "tests/unit" "tests/integration" "specs/contracts" "state"; do
  if [ ! -d "$PROJECT_ROOT/$dir" ]; then
    echo "ERROR: Directory $PROJECT_ROOT/$dir was not created"
    exit 1
  fi
done

echo "All directories created successfully"

# Run tree command to generate directory structure
tree -L 3 "$PROJECT_ROOT" > "$PROJECT_ROOT/data/processed/dir_structure.txt" 2>/dev/null || {
  # Fallback if tree is not available
  find "$PROJECT_ROOT" -maxdepth 3 -type d | sort > "$PROJECT_ROOT/data/processed/dir_structure.txt"
}

# Verify the output file exists and contains expected entries
if [ ! -f "$PROJECT_ROOT/data/processed/dir_structure.txt" ]; then
  echo "ERROR: dir_structure.txt was not created"
  exit 1
fi

# Check that all five top-level directories are mentioned in the output
for dir_name in "data" "code" "tests" "specs" "state"; do
  if ! grep -q "$dir_name" "$PROJECT_ROOT/data/processed/dir_structure.txt"; then
    echo "ERROR: Directory name '$dir_name' not found in dir_structure.txt"
    exit 1
  fi
done

echo "Verification passed: dir_structure.txt contains all required directories"
echo "Contents of dir_structure.txt:"
cat "$PROJECT_ROOT/data/processed/dir_structure.txt"