#!/bin/bash
set -e

PROJECT_ROOT="projects/PROJ-881-llmxive-follow-up-extending-efficientrol"
CODE_ROOT="${PROJECT_ROOT}/code"

# Phase 1: Create root project directory structure
mkdir -p "${CODE_ROOT}"
mkdir -p "${CODE_ROOT}/tests"
mkdir -p "${CODE_ROOT}/data"
mkdir -p "${CODE_ROOT}/docs"
mkdir -p "${CODE_ROOT}/scripts"
mkdir -p "${CODE_ROOT}/results"
mkdir -p "${CODE_ROOT}/specs/001-entropy-validity-prediction/contracts"

# Phase 1: Create source subdirectories within code root
mkdir -p "${CODE_ROOT}/src"
mkdir -p "${CODE_ROOT}/src/utils"
mkdir -p "${CODE_ROOT}/src/data"
mkdir -p "${CODE_ROOT}/src/generation"
mkdir -p "${CODE_ROOT}/src/analysis"
mkdir -p "${CODE_ROOT}/logs"

# Verify structure
REQUIRED_DIRS=(
  "${CODE_ROOT}"
  "${CODE_ROOT}/tests"
  "${CODE_ROOT}/data"
  "${CODE_ROOT}/docs"
  "${CODE_ROOT}/scripts"
  "${CODE_ROOT}/results"
  "${CODE_ROOT}/specs/001-entropy-validity-prediction/contracts"
  "${CODE_ROOT}/src"
  "${CODE_ROOT}/src/utils"
  "${CODE_ROOT}/src/data"
  "${CODE_ROOT}/src/generation"
  "${CODE_ROOT}/src/analysis"
  "${CODE_ROOT}/logs"
)

MISSING=0
for dir in "${REQUIRED_DIRS[@]}"; do
  if [ ! -d "$dir" ]; then
    echo "Missing directory: $dir"
    MISSING=1
  fi
done

if [ $MISSING -eq 1 ]; then
  echo "Structure creation failed"
  exit 1
fi

echo "Structure created"

# Generate project_structure.log with absolute paths
LOG_FILE="${CODE_ROOT}/../project_structure.log"
python3 -c "
import json
import os

dirs = [
    '${CODE_ROOT}',
    '${CODE_ROOT}/tests',
    '${CODE_ROOT}/data',
    '${CODE_ROOT}/docs',
    '${CODE_ROOT}/scripts',
    '${CODE_ROOT}/results',
    '${CODE_ROOT}/specs/001-entropy-validity-prediction/contracts',
    '${CODE_ROOT}/src',
    '${CODE_ROOT}/src/utils',
    '${CODE_ROOT}/src/data',
    '${CODE_ROOT}/src/generation',
    '${CODE_ROOT}/src/analysis',
    '${CODE_ROOT}/logs'
]

# Convert to absolute paths
abs_paths = [os.path.abspath(d) for d in dirs]

with open('${LOG_FILE}', 'w') as f:
    json.dump(abs_paths, f, indent=2)
"