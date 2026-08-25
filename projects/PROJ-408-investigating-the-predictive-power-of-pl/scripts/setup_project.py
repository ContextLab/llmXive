"""
Project Initialization Script for llmXive - PROJ-408
Executes T001b: Initialize the repository structure by creating required directories.
"""
import os
import sys
from pathlib import Path

def setup_project():
    """
    Create the standard directory structure for the project.
    Based on T001a specification:
    - code/
    - data/raw/
    - data/processed/
    - output/figures/
    - output/reports/
    - tests/
    - tests/contract/schemas/
    """
    # Define the project root (assuming this script is in scripts/)
    # We assume the script is run from the project root or the path is relative to cwd
    project_root = Path.cwd()
    
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "output/figures",
        "output/reports",
        "tests",
        "tests/contract/schemas",
        "state/projects", # Added for T021 checksum storage
        "docs"            # Added for T034 documentation
    ]

    created_count = 0
    skipped_count = 0

    print(f"Initializing project structure in: {project_root}")

    for dir_path in directories:
        full_path = project_root / dir_path
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            if full_path.exists() and full_path.is_dir():
                # Check if it was just created or already existed
                # Since exist_ok=True, we can't easily distinguish 'created' vs 'existed' 
                # without checking modification time, but for setup scripts, 
                # 'exist_ok' success is usually sufficient.
                # We'll count it as created if it wasn't there before the call, 
                # but since we can't easily know, we'll just report success.
                print(f"  [OK] Directory ready: {dir_path}")
                created_count += 1
            else:
                print(f"  [WARN] Path exists but is not a directory: {full_path}")
        except OSError as e:
            print(f"  [FAIL] Could not create directory {dir_path}: {e}")
            return 1

    print(f"\nInitialization complete. Created/Verified {created_count} directories.")
    return 0

if __name__ == "__main__":
    sys.exit(setup_project())
