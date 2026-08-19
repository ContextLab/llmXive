"""
Script to initialize the project directory structure and placeholder files.
This script creates the required directories and .gitkeep files as per T001a and T001b.
"""
import os
import sys
from pathlib import Path

def main():
    """Create the project directory structure and placeholder files."""
    # Define the project root (current working directory)
    root = Path.cwd()

    # Define the required directories relative to the root
    # Based on T001a: code/, data/raw/, data/derived/, tests/, specs/, results/, docs/
    directories = [
        "code",
        "data/raw",
        "data/derived",
        "tests",
        "specs",
        "results",
        "docs",
        # Additional utility directories often needed for full pipeline
        "results/plots",
        "results/error",
        "state",
        "state/projects",
    ]

    created_count = 0
    for dir_path in directories:
        full_path = root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory exists: {full_path}")

    # Define directories that need .gitkeep files (T001b)
    # Specifically data directories to ensure they are tracked by git
    data_dirs = [
        "data/raw",
        "data/derived",
    ]

    keep_count = 0
    for dir_name in data_dirs:
        dir_path = root / dir_name
        if dir_path.exists():
            gitkeep_path = dir_path / ".gitkeep"
            if not gitkeep_path.exists():
                gitkeep_path.touch()
                print(f"Created placeholder: {gitkeep_path}")
                keep_count += 1
            else:
                print(f"Placeholder exists: {gitkeep_path}")
        else:
            print(f"Warning: Data directory missing for placeholder: {dir_path}")

    print(f"\nSetup complete. Created {created_count} directories and {keep_count} placeholders.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
