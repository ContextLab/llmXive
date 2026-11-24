#!/usr/bin/env bash
# Setup script for the molecular permeability project.
# Creates all required directories under the project root.
set -e

# List of directories to create
DIRS=(
  "data/raw"
  "data/processed"
  "data/interim"
  "data/results"
  "data/logs"
  "figures"
  "results"
  "code/data"
  "code/models"
  "code/analysis"
  "tests/unit"
  "tests/integration"
)

for d in "${DIRS[@]}"; do
  mkdir -p "$d"
  echo "Created directory: $d"
done

echo "All required directories have been created."
