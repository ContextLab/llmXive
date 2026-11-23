#!/bin/bash
set -e

# Define project root relative to script location or current directory
# Assuming this script is run from repository root
PROJECT_ROOT="projects/PROJ-881-llmxive-follow-up-extending-efficientrol"

echo "Creating project directory structure for $PROJECT_ROOT..."

# Create main directories
mkdir -p "$PROJECT_ROOT/code"
mkdir -p "$PROJECT_ROOT/tests"
mkdir -p "$PROJECT_ROOT/data"
mkdir -p "$PROJECT_ROOT/docs"
mkdir -p "$PROJECT_ROOT/scripts"
mkdir -p "$PROJECT_ROOT/results"
mkdir -p "$PROJECT_ROOT/specs/001-entropy-validity-prediction/contracts"

# Create subdirectories under code
mkdir -p "$PROJECT_ROOT/code/src"
mkdir -p "$PROJECT_ROOT/code/data/raw"
mkdir -p "$PROJECT_ROOT/code/data/processed"
mkdir -p "$PROJECT_ROOT/code/artifacts"
mkdir -p "$PROJECT_ROOT/code/state"
mkdir -p "$PROJECT_ROOT/code/logs"
mkdir -p "$PROJECT_ROOT/code/contracts"

# Create subdirectories under tests
mkdir -p "$PROJECT_ROOT/tests/unit"
mkdir -p "$PROJECT_ROOT/tests/integration"
mkdir -p "$PROJECT_ROOT/tests/contract"

# Create subdirectories under specs
mkdir -p "$PROJECT_ROOT/specs/001-entropy-validity-prediction"

echo "Directory structure created successfully."
echo "Listing structure:"
find "$PROJECT_ROOT" -type d | sort
