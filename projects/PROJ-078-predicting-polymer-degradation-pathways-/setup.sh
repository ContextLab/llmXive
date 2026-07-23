#!/bin/bash
# setup.sh - Automate directory creation and verify existence for PROJ-078
#
# This script ensures the project structure matches the requirements:
# - code/
# - data/raw/
# - data/processed/
# - data/reports/
# - tests/
# - state/

set -e  # Exit immediately if a command exits with a non-zero status

echo "🚀 Starting project setup for PROJ-078..."

# Determine the script directory and project root
# This script is expected to be in the project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$SCRIPT_DIR"

# Define directories relative to project root
DIRECTORIES=(
    "code"
    "data/raw"
    "data/processed"
    "data/reports"
    "tests"
    "state"
)

echo "📂 Checking/Creating directories in: $PROJECT_ROOT"

FAILED=0

for dir in "${DIRECTORIES[@]}"; do
    full_path="$PROJECT_ROOT/$dir"
    
    if [ ! -d "$full_path" ]; then
        echo "  ➕ Creating: $full_path"
        mkdir -p "$full_path"
    else
        if [ ! -d "$full_path" ]; then
            echo "  ❌ Error: $full_path exists but is not a directory!"
            FAILED=1
        else
            echo "  ✅ Exists: $full_path"
        fi
    fi
done

if [ $FAILED -eq 0 ]; then
    echo ""
    echo "🎉 Verification successful. All required directories exist."
    
    # Optional: Run the Python verification script if it exists
    if [ -f "$PROJECT_ROOT/code/setup_project.py" ]; then
        echo "🐍 Running Python verification script..."
        python3 "$PROJECT_ROOT/code/setup_project.py"
    fi
else
    echo ""
    echo "❌ Setup failed. Check the errors above."
    exit 1
fi

echo "✅ Setup complete."
