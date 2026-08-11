#!/bin/bash
# init_structure.sh - Automate directory creation and initial file scaffolding
#
# This script creates the standard project directory structure for the
# molecular complexity prediction pipeline and scaffolds initial files.
#
# Usage: ./scripts/init_structure.sh [project_root]
# If project_root is not provided, the current directory is used.

set -e  # Exit on error

# Determine project root
PROJECT_ROOT="${1:-.}"
PROJECT_ROOT="$(cd "$PROJECT_ROOT" && pwd)"

echo "Initializing project structure in: $PROJECT_ROOT"

# Define directories to create
DIRS=(
    "data/raw"
    "data/processed"
    "results/models"
    "results/reports"
    "results/plots"
    "code"
    "tests"
)

# Create directories
for dir in "${DIRS[@]}"; do
    full_path="$PROJECT_ROOT/$dir"
    if [ -d "$full_path" ]; then
        echo "  [SKIP] $dir (already exists)"
    else
        mkdir -p "$full_path"
        echo "  [CREATED] $dir"
    fi
done

# Scaffold initial files (if they don't exist)
echo "Scaffolding initial files..."

# Create __init__.py in code and tests if missing
if [ ! -f "$PROJECT_ROOT/code/__init__.py" ]; then
    touch "$PROJECT_ROOT/code/__init__.py"
    echo "  [CREATED] code/__init__.py"
fi

if [ ! -f "$PROJECT_ROOT/tests/__init__.py" ]; then
    touch "$PROJECT_ROOT/tests/__init__.py"
    echo "  [CREATED] tests/__init__.py"
fi

# Create .gitkeep in data directories to ensure they are tracked by git
for dir in "data/raw" "data/processed"; do
    if [ ! -f "$PROJECT_ROOT/$dir/.gitkeep" ]; then
        touch "$PROJECT_ROOT/$dir/.gitkeep"
        echo "  [CREATED] $dir/.gitkeep"
    fi
done

echo "Project structure initialization complete."
