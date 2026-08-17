"""
Script to create the required directory structure for the project.
Implements Task T001a.
"""
import os
import sys
from pathlib import Path

def main():
    """Create the project directory structure."""
    # Define the project root (current directory)
    root = Path(__file__).resolve().parent.parent

    # Define required directories relative to the project root
    # Based on tasks.md T001a: src/, tests/, data/raw/, data/processed/, models/, templates/
    # Also adding standard ML project dirs: data/interim/, figures/, reports/ for robustness
    dirs_to_create = [
        "src",
        "tests",
        "data/raw",
        "data/processed",
        "data/interim",
        "models",
        "templates",
        "figures",
        "reports",
        "code", # Ensure 'code' exists as we are running from within it or relative to it
    ]

    created_count = 0
    skipped_count = 0

    for dir_path in dirs_to_create:
        full_path = root / dir_path
        try:
            if full_path.exists():
                print(f"Skipping existing directory: {full_path}")
                skipped_count += 1
            else:
                full_path.mkdir(parents=True, exist_ok=True)
                print(f"Created directory: {full_path}")
                created_count += 1
        except PermissionError:
            print(f"Permission denied creating directory: {full_path}")
            return 1
        except Exception as e:
            print(f"Error creating directory {full_path}: {e}")
            return 1

    print(f"\nDirectory creation complete.")
    print(f"Created: {created_count}, Skipped (existing): {skipped_count}")
    
    # Verify the specific requirement from T001a
    required_dirs = ["src", "tests", "data/raw", "data/processed", "models", "templates"]
    missing = []
    for d in required_dirs:
        if not (root / d).exists():
            missing.append(d)
    
    if missing:
        print(f"ERROR: Required directories missing after creation attempt: {missing}")
        return 1
    
    print("All required directories verified.")
    return 0

if __name__ == "__main__":
    sys.exit(main())