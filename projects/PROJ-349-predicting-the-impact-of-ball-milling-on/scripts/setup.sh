#!/bin/bash
# Setup script for PROJ-349-predicting-the-impact-of-ball-milling-on
# Creates the directory structure listed in scripts/setup_manifest.txt

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "Creating project directory structure in: $PROJECT_ROOT"

# Core project directories
mkdir -p "$PROJECT_ROOT/src"
mkdir -p "$PROJECT_ROOT/tests"
mkdir -p "$PROJECT_ROOT/data/raw"
mkdir -p "$PROJECT_ROOT/data/processed"
mkdir -p "$PROJECT_ROOT/data/splits"
mkdir -p "$PROJECT_ROOT/results"
mkdir -p "$PROJECT_ROOT/contracts"
mkdir -p "$PROJECT_ROOT/specs"
mkdir -p "$PROJECT_ROOT/scripts"
mkdir -p "$PROJECT_ROOT/docs"
mkdir -p "$PROJECT_ROOT/figures"

# GitHub Actions workflows
mkdir -p "$PROJECT_ROOT/.github/workflows"

# Specific subdirectories for organization
mkdir -p "$PROJECT_ROOT/src/cli"
mkdir -p "$PROJECT_ROOT/src/config"
mkdir -p "$PROJECT_ROOT/src/evaluate"
mkdir -p "$PROJECT_ROOT/src/exceptions"
mkdir -p "$PROJECT_ROOT/src/ingest"
mkdir -p "$PROJECT_ROOT/src/interpret"
mkdir -p "$PROJECT_ROOT/src/model"
mkdir -p "$PROJECT_ROOT/src/preprocess"
mkdir -p "$PROJECT_ROOT/src/utils"

mkdir -p "$PROJECT_ROOT/tests/contract"
mkdir -p "$PROJECT_ROOT/tests/integration"
mkdir -p "$PROJECT_ROOT/tests/unit"

echo "Directory structure created successfully."
echo "You can verify with: ls -R $PROJECT_ROOT"