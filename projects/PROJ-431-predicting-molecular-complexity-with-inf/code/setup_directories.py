"""
Script to initialize the project directory structure for the molecular complexity prediction pipeline.
Creates standard data science directories: raw data, processed data, models, reports, plots, code, and tests.
"""
import os
import sys
from pathlib import Path

def main():
    """Create the standard project directory structure."""
    # Define the root directory (current working directory or specified path)
    root = Path.cwd()
    
    # Define the required directories relative to the root
    directories = [
        "data/raw",
        "data/processed",
        "results/models",
        "results/reports",
        "results/plots",
        "code",
        "tests"
    ]
    
    created_count = 0
    skipped_count = 0
    
    print(f"Initializing project structure in: {root}")
    
    for dir_path in directories:
        full_path = root / dir_path
        if full_path.exists():
            print(f"  [SKIP] {dir_path} (already exists)")
            skipped_count += 1
        else:
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"  [CREATED] {dir_path}")
            created_count += 1
    
    print(f"\nDone. Created {created_count} directories, skipped {skipped_count}.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
