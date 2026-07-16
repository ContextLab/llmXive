"""
Setup script for llmXive data directory structure.

This script creates the required directory hierarchy for the project:
- data/raw/          : Raw, unprocessed data from external sources
- data/derived/      : Processed data, intermediate results, and artifacts
- data/gold_standard/: Human annotations and ground truth data
- artifacts/         : Model checkpoints, logs, and experiment artifacts

The script is idempotent and will not fail if directories already exist.
"""
import os
from pathlib import Path

# Define the base project root (assumed to be the parent of the code/ directory)
# In a standard setup, this script is at code/setup_data_dirs.py
PROJECT_ROOT = Path(__file__).parent.parent

# Define the directory structure relative to PROJECT_ROOT
DIRECTORIES = [
    "data/raw",
    "data/derived",
    "data/gold_standard",
    "artifacts",
]

def setup_directories():
    """Create the required data directory structure."""
    created_dirs = []
    skipped_dirs = []

    for dir_path_str in DIRECTORIES:
        dir_path = PROJECT_ROOT / dir_path_str
        
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(str(dir_path.relative_to(PROJECT_ROOT)))
            print(f"Created: {dir_path.relative_to(PROJECT_ROOT)}")
        else:
            skipped_dirs.append(str(dir_path.relative_to(PROJECT_ROOT)))
            # Only print if it's not just a parent directory check
            # We want to be quiet if it exists but not necessarily "created"
            # But for a setup script, a little feedback is good.
            # Let's only print if it's explicitly a leaf we checked.
            pass

    # Summary
    if created_dirs:
        print(f"\nSuccessfully created {len(created_dirs)} directory(ies).")
    else:
        print("\nAll required directories already exist.")

    if skipped_dirs:
        print(f"Skipped (already exist): {', '.join(skipped_dirs)}")

    return created_dirs, skipped_dirs

if __name__ == "__main__":
    print(f"Setting up data directories for llmXive project at: {PROJECT_ROOT}")
    print("-" * 50)
    setup_directories()
    print("-" * 50)
    print("Setup complete.")