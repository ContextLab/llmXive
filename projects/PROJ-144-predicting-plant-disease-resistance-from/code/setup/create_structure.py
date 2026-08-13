"""
Script to create the project directory structure for llmXive plant disease resistance project.
Ensures all required directories exist and are writable.
"""
import os
import sys
from pathlib import Path

# Define the project root (assumed to be the parent of 'code' or current dir if running from root)
# We assume this script is run from the project root.
PROJECT_ROOT = Path.cwd()

# List of directories to create relative to PROJECT_ROOT
REQUIRED_DIRS = [
    "code",
    "code/data",
    "code/modeling",
    "code/utils",
    "code/research",
    "code/setup",
    "data/raw",
    "data/processed",
    "data/intermediate",
    "tests",
    "tests/unit",
    "tests/integration",
    "state",
    "results",
    "results/plots",
    "contracts",
]

def create_structure():
    """Create all required directories if they do not exist."""
    created_count = 0
    existing_count = 0
    failed_count = 0

    print(f"Creating project structure at: {PROJECT_ROOT}")

    for dir_path_str in REQUIRED_DIRS:
        dir_path = PROJECT_ROOT / dir_path_str
        try:
            if not dir_path.exists():
                dir_path.mkdir(parents=True, exist_ok=True)
                print(f"Created: {dir_path}")
                created_count += 1
            else:
                # Verify writability
                test_file = dir_path / ".write_test"
                try:
                    test_file.touch()
                    test_file.unlink()
                    existing_count += 1
                except PermissionError:
                    print(f"ERROR: Directory {dir_path} exists but is not writable.")
                    failed_count += 1
        except Exception as e:
            print(f"ERROR: Failed to create {dir_path}: {e}")
            failed_count += 1

    print(f"\nSummary:")
    print(f"  Created: {created_count}")
    print(f"  Existing & Writable: {existing_count}")
    print(f"  Failed: {failed_count}")

    if failed_count > 0:
        sys.exit(1)
    else:
        print("Structure creation successful.")

if __name__ == "__main__":
    create_structure()