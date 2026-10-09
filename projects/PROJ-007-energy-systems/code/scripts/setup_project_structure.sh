#!/usr/bin/env bash
# T001: Create the project directory structure.
# Creates: src/data src/analysis src/utils src/models
#          tests/unit tests/integration
#          data/raw data/processed data/outputs specs/
set -e

cd "$(dirname "$0")/../.."   # project root (parent of code/)

mkdir -p src/data src/analysis src/utils src/models \
         tests/unit tests/integration \
         data/raw data/processed data/outputs \
         specs/

# Ensure package initializers exist so `src.*` imports resolve.
touch src/__init__.py src/data/__init__.py src/analysis/__init__.py \
      src/utils/__init__.py src/models/__init__.py
touch tests/__init__.py tests/unit/__init__.py tests/integration/__init__.py

echo "Project structure created:"
for d in src/data src/analysis src/utils src/models \
         tests/unit tests/integration \
         data/raw data/processed data/outputs specs/; do
  if [ -d "$d" ]; then
    echo "  OK  $d"
  else
    echo "  MISSING  $d" >&2
    exit 1
  fi
done