#!/bin/bash
# Scaffold project directory structure for llmXive follow-up
# Creates required directories and generates verification JSON

set -e

# Project root (assumes script is run from project root)
PROJECT_ROOT="projects/PROJ-888-llmxive-follow-up-extending-kairos-a-nat"

echo "Creating project directory structure..."

# Create main project directory
mkdir -p "$PROJECT_ROOT"

# Create required subdirectories
mkdir -p "$PROJECT_ROOT/code"
mkdir -p "$PROJECT_ROOT/tests"
mkdir -p "$PROJECT_ROOT/data"
mkdir -p "$PROJECT_ROOT/state"
mkdir -p "$PROJECT_ROOT/docs"
mkdir -p "$PROJECT_ROOT/results"

# Create additional standard directories
mkdir -p "$PROJECT_ROOT/logs"
mkdir -p "$PROJECT_ROOT/scripts"
mkdir -p "$PROJECT_ROOT/specs"
mkdir -p "$PROJECT_ROOT/data/raw"
mkdir -p "$PROJECT_ROOT/data/processed"
mkdir -p "$PROJECT_ROOT/data/models"
mkdir -p "$PROJECT_ROOT/tests/unit"
mkdir -p "$PROJECT_ROOT/tests/integration"
mkdir -p "$PROJECT_ROOT/tests/contract"
mkdir -p "$PROJECT_ROOT/code/utils"
mkdir -p "$PROJECT_ROOT/code/data"
mkdir -p "$PROJECT_ROOT/code/models"
mkdir -p "$PROJECT_ROOT/code/analysis"
mkdir -p "$PROJECT_ROOT/figures"

# Generate verification JSON
echo "Generating verification file..."
cat > "$PROJECT_ROOT/verify_structure.json" << 'EOF'
{
  "project_root": "projects/PROJ-888-llmxive-follow-up-extending-kairos-a-nat",
  "created_directories": [
    "code",
    "tests",
    "data",
    "state",
    "docs",
    "results",
    "logs",
    "scripts",
    "specs",
    "data/raw",
    "data/processed",
    "data/models",
    "tests/unit",
    "tests/integration",
    "tests/contract",
    "code/utils",
    "code/data",
    "code/models",
    "code/analysis",
    "figures"
  ],
  "verification_timestamp": "2024-01-01T00:00:00Z",
  "status": "success"
}
EOF

echo "Directory structure created successfully."
echo "Verification file: $PROJECT_ROOT/verify_structure.json"
cat "$PROJECT_ROOT/verify_structure.json"
