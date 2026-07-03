#!/bin/bash
# Setup directories for PROJ-442

set -e

echo "Creating project directories..."

mkdir -p data/raw
mkdir -p data/processed
mkdir -p data/models
mkdir -p data/logs
mkdir -p src/data
mkdir -p src/modeling
mkdir -p src/utils
mkdir -p tests/unit
mkdir -p tests/integration
mkdir -p tests/contract
mkdir -p scripts
mkdir -p state/projects

echo "Directory structure created successfully."
echo "Created:"
ls -la data/
ls -la src/
ls -la tests/
ls -la state/