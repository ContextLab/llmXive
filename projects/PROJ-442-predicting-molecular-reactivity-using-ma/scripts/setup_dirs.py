"""
Setup script to create the project directory structure for PROJ-442.
Replaces the shell script `scripts/setup_dirs.sh` with a Python equivalent
to ensure cross-platform compatibility and better integration with the
Python-based pipeline.
"""
import os
import sys
from pathlib import Path

# Define the project root (parent of this script's directory)
# This script is located at scripts/setup_dirs.py
# Project root is the directory containing 'scripts', 'src', 'data', etc.
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# List of directories to create relative to PROJECT_ROOT
DIRECTORIES = [
    "data/raw",
    "data/processed",
    "data/models",
    "src/data",
    "src/modeling",
    "src/utils",
    "tests/unit",
    "tests/integration",
    "tests/contract",
    "scripts",
]

def main():
    print(f"Setting up project directories at: {PROJECT_ROOT}")
    created_count = 0
    
    for dir_path in DIRECTORIES:
        full_path = PROJECT_ROOT / dir_path
        
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created: {full_path}")
            created_count += 1
        else:
            print(f"Exists:  {full_path}")
    
    print(f"\nSetup complete. {created_count} new directories created.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
