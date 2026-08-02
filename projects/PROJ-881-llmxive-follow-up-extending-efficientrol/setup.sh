#!/bin/bash
# Setup script for PROJ-881-llmxive-follow-up-extending-efficientrol
# Creates the required directory structure for the project.
# Run from the repository root.

set -e

# Define the project root relative to the current directory
PROJECT_ROOT="projects/PROJ-881-llmxive-follow-up-extending-efficientrol"

echo "Creating project directory structure for $PROJECT_ROOT..."

# Create main project directories
mkdir -p "$PROJECT_ROOT/code"
mkdir -p "$PROJECT_ROOT/tests"
mkdir -p "$PROJECT_ROOT/data"
mkdir -p "$PROJECT_ROOT/docs"
mkdir -p "$PROJECT_ROOT/scripts"
mkdir -p "$PROJECT_ROOT/results"
mkdir -p "$PROJECT_ROOT/specs/001-entropy-validity-prediction/contracts"

# Create code subdirectories
mkdir -p "$PROJECT_ROOT/code/src"
mkdir -p "$PROJECT_ROOT/code/data/raw"
mkdir -p "$PROJECT_ROOT/code/data/processed"
mkdir -p "$PROJECT_ROOT/code/artifacts"
mkdir -p "$PROJECT_ROOT/code/state"

# Create additional standard directories if not covered above
# Ensuring logs directory exists for generation logs
mkdir -p "$PROJECT_ROOT/code/logs"

# Create test subdirectories
mkdir -p "$PROJECT_ROOT/tests/unit"
mkdir -p "$PROJECT_ROOT/tests/integration"
mkdir -p "$PROJECT_ROOT/tests/contract"

echo "Directory structure created successfully."
echo "Project root: $PROJECT_ROOT"
ls -R "$PROJECT_ROOT"