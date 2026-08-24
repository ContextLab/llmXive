"""
Script to create the project directory structure for llmXive.
Ensures deterministic creation of all required folders.
"""
import os
import sys
from pathlib import Path

def main():
    """Create all required project directories."""
    # Define the root directory (current working directory or specified path)
    root = Path.cwd()
    
    # List of directories to create relative to root
    # Based on task T001a requirements:
    # code/, data/, data/raw, data/processed, data/logs, tests/, artifacts/, figures/
    directories = [
        "code",
        "data",
        "data/raw",
        "data/processed",
        "data/logs",
        "tests",
        "artifacts",
        "figures",
        # Additional standard directories often needed, ensuring alignment with project structure
        "code/utils",
        "code/ingestion",
        "code/modeling",
        "specs",
        "specs/001-predict-root-architecture",
        "specs/001-predict-root-architecture/contracts",
    ]

    created_count = 0
    skipped_count = 0

    for dir_path in directories:
        full_path = root / dir_path
        try:
            # exist_ok=True ensures we don't fail if directory already exists
            full_path.mkdir(parents=True, exist_ok=True)
            if full_path.is_dir():
                print(f"Created directory: {full_path}")
                created_count += 1
            else:
                # This case should ideally not happen with mkdir but good for safety
                print(f"Warning: {full_path} exists but is not a directory.")
        except PermissionError:
            print(f"Error: Permission denied when creating {full_path}")
            sys.exit(1)
        except OSError as e:
            print(f"Error: Could not create {full_path}: {e}")
            sys.exit(1)

    print(f"\nDirectory creation complete.")
    print(f"Created: {created_count} directories.")
    print(f"Skipped (already exist): {skipped_count} directories.")

if __name__ == "__main__":
    main()