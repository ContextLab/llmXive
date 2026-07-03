"""
Script to initialize the project directory structure for PROJ-180.

Creates the required directories as per tasks.md Task T001a:
- code/
- data/raw
- data/processed
- results
- specs/

This script ensures the project tree exists before any data acquisition or
analysis scripts are run.
"""
import os
import sys
from pathlib import Path

def main():
    # Define the project root (current working directory)
    project_root = Path.cwd()
    
    # Define the required directories relative to the project root
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "results",
        "specs"
    ]
    
    created_count = 0
    skipped_count = 0
    
    print(f"Initializing directory structure in: {project_root}")
    
    for dir_path in directories:
        full_path = project_root / dir_path
        
        if full_path.exists():
            print(f"  [SKIP] {dir_path} (already exists)")
            skipped_count += 1
        else:
            try:
                full_path.mkdir(parents=True, exist_ok=True)
                print(f"  [CREATE] {dir_path}")
                created_count += 1
            except OSError as e:
                print(f"  [ERROR] Failed to create {dir_path}: {e}", file=sys.stderr)
                sys.exit(1)
    
    print(f"\nDone. Created {created_count} directories, skipped {skipped_count}.")
    
    # Verify structure
    missing = []
    for dir_path in directories:
        if not (project_root / dir_path).exists():
            missing.append(dir_path)
    
    if missing:
        print(f"Warning: The following directories are missing: {missing}", file=sys.stderr)
        sys.exit(1)
    else:
        print("Verification passed: All required directories exist.")

if __name__ == "__main__":
    main()
