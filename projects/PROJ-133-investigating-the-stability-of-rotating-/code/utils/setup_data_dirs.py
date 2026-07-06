"""
Setup utility to initialize the project's data directory structure.

This script creates the required subdirectories under `data/` as specified
in the project's data model and task requirements:
- data/raw: For unprocessed, downloaded, or raw simulation output files.
- data/processed: For cleaned, normalized, or intermediate analysis data.
- data/aggregated: For final statistical aggregates, phase maps, and report data.

It is idempotent: running it multiple times will not error if directories exist.
"""
import os
import sys
from pathlib import Path

# Define the project root relative to this script's location
# Assuming this script is at code/utils/setup_data_dirs.py
# Project root is two levels up: code/utils -> code -> root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_ROOT = PROJECT_ROOT / "data"

SUBDIRECTORIES = [
    "raw",
    "processed",
    "aggregated",
]

def main():
    """Create the data directory structure if it doesn't exist."""
    if not DATA_ROOT.exists():
        print(f"Creating base data directory: {DATA_ROOT}")
        DATA_ROOT.mkdir(parents=True, exist_ok=True)
    else:
        print(f"Data directory already exists: {DATA_ROOT}")

    for subdir_name in SUBDIRECTORIES:
        subdir_path = DATA_ROOT / subdir_name
        if not subdir_path.exists():
            subdir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created: {subdir_path}")
        else:
            print(f"Directory already exists: {subdir_path}")

    print("Data directory setup complete.")
    return 0

if __name__ == "__main__":
    sys.exit(main())