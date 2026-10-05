"""
Script to initialize the project directory structure for the gut microbiome
and cognitive flexibility study.

Creates the following directories at the repository root:
- src/
- tests/
- data/raw
- data/processed
- data/results
- logs/
"""
import os
import sys
from pathlib import Path

def main():
    # Define the project root (assuming script is in code/scripts/)
    # We need to go up two levels to reach the repository root
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent.parent

    directories = [
        "src",
        "tests",
        "data/raw",
        "data/processed",
        "data/results",
        "logs"
    ]

    created_count = 0
    for dir_name in directories:
        dir_path = project_root / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {dir_path}")

    print(f"\nInitialization complete. {created_count} new directory(ies) created.")
    return 0

if __name__ == "__main__":
    sys.exit(main())