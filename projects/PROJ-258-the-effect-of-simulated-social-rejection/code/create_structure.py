import os
import sys
from pathlib import Path

def main():
    """
    Creates the required project directory structure for PROJ-258.
    This script ensures the existence of:
    - code/
    - data/raw/
    - data/interim/
    - data/processed/
    - tests/
    """
    # Define the root directory (current working directory or project root)
    # We assume this script is run from the project root.
    root = Path.cwd()

    required_dirs = [
        "code",
        "data/raw",
        "data/interim",
        "data/processed",
        "tests",
        "docs",
        "reports",
        "specs",
        ".github/workflows"
    ]

    created_count = 0
    existing_count = 0

    for dir_path in required_dirs:
        full_path = root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            existing_count += 1
            # Optional: Verify it is a directory
            if not full_path.is_dir():
                raise NotADirectoryError(f"Path exists but is not a directory: {full_path}")

    print(f"Structure verification complete. Created: {created_count}, Existing: {existing_count}")
    
    # Verify specific critical paths exist for the pipeline
    critical_paths = [
        root / "data" / "raw",
        root / "data" / "interim",
        root / "data" / "processed",
        root / "code",
        root / "tests"
    ]
    
    for p in critical_paths:
        if not p.exists():
            raise FileNotFoundError(f"Critical path missing after creation attempt: {p}")

    print("All critical paths verified.")

if __name__ == "__main__":
    main()