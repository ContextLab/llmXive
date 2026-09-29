import os
import sys
from pathlib import Path

def main():
    """
    Create the project directory structure as defined in the implementation plan.
    
    Addresses FR-001, SC-004.
    """
    # Define the relative paths to create
    # All paths are relative to the project root (assumed to be the current working directory)
    directories = [
        "src/data",
        "src/analysis",
        "src/utils",
        "src/cli",
        "tests/unit",
        "tests/integration",
        "data/raw",
        "data/processed",
        "data/results",
        "results",
        "state"
    ]

    created_count = 0
    existing_count = 0

    for dir_path in directories:
        path = Path(dir_path)
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            # Check if it is indeed a directory
            if path.is_dir():
                print(f"Directory already exists: {dir_path}")
                existing_count += 1
            else:
                print(f"ERROR: Path exists but is not a directory: {dir_path}")
                sys.exit(1)

    print(f"\nProject structure initialization complete.")
    print(f"  Created: {created_count} new directories")
    print(f"  Existing: {existing_count} directories")

    # Verify structure
    missing = []
    for dir_path in directories:
        if not Path(dir_path).is_dir():
            missing.append(dir_path)
    
    if missing:
        print(f"\nFATAL: The following directories were not created: {missing}")
        sys.exit(1)
    else:
        print("Verification passed: All required directories exist.")

if __name__ == "__main__":
    main()