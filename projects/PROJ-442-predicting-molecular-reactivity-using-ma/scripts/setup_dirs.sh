#!/bin/bash
# Setup directory structure for the molecular reactivity project

DIRS=(
    "data/raw"
    "data/processed"
    "data/models"
    "src/data"
    "src/modeling"
    "src/utils"
    "tests/unit"
    "tests/integration"
    "tests/contract"
    "scripts"
    "state/projects"
    "figures"
)

for dir in "${DIRS[@]}"; do
    if [ ! -d "$dir" ]; then
        mkdir -p "$dir"
        echo "Created directory: $dir"
    else
        echo "Directory exists: $dir"
    fi
done

# Create placeholder __init__.py files for Python packages
for dir in src data tests tests/unit tests/integration tests/contract src/data src/modeling src/utils; do
    if [ -d "$dir" ] && [ ! -f "$dir/__init__.py" ]; then
        touch "$dir/__init__.py"
        echo "Created __init__.py in $dir"
    fi
done

echo "Directory setup complete."
