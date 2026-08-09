#!/bin/bash
set -e

echo "Starting PROJ-756 Pipeline..."

# Ensure project structure exists (idempotent)
python -c "
from pathlib import Path
dirs = [
    'data', 'data/raw', 'data/processed', 'data/synthetic',
    'code', 'tests', 'artifacts', 'results', 'state',
    'logs', 'logs/archive'
]
for d in dirs:
    Path(d).mkdir(parents=True, exist_ok=True)
# Ensure __init__.py files
for d in ['code', 'tests', 'data', 'artifacts', 'results', 'state', 'logs', 'logs/archive']:
    (Path(d) / '__init__.py').touch(exist_ok=True)
# Ensure .gitkeep in data subdirs
for d in ['data/raw', 'data/processed', 'data/synthetic']:
    (Path(d) / '.gitkeep').touch(exist_ok=True)
"

# Run main pipeline entry point
python code/main.py --full-pipeline

echo "Pipeline execution complete."
