import os
import sys
from pathlib import Path

def main():
    """
    Creates the required project directory structure for llmXive PROJ-458.
    
    This script implements Task T001: Create project structure.
    It ensures the following directories exist relative to the project root:
    - code/utils
    - data/raw
    - data/processed
    - data/results
    - data/metadata
    - tests/unit
    - tests/integration
    - docs
    """
    # Define the project root (parent of code/ directory)
    # We assume this script is run from the project root or the code/ directory.
    # To be robust, we find the directory containing this script and look for 'code' or treat script dir as root.
    script_dir = Path(__file__).resolve().parent
    
    # If the script is in 'code/', the root is parent. If it's in root, root is script_dir.
    if script_dir.name == 'code':
        root_dir = script_dir.parent
    else:
        # Fallback: assume script is at root or we create 'code' inside current
        root_dir = script_dir

    # Define relative paths to create
    dirs_to_create = [
        "code/utils",
        "data/raw",
        "data/processed",
        "data/results",
        "data/metadata",
        "tests/unit",
        "tests/integration",
        "docs"
    ]

    created_count = 0
    skipped_count = 0

    print(f"Project root identified at: {root_dir}")
    print("Creating project structure...")

    for dir_path in dirs_to_create:
        full_path = root_dir / dir_path
        if full_path.exists():
            print(f"  [SKIP] {dir_path} (already exists)")
            skipped_count += 1
        else:
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"  [CREATE] {dir_path}")
            created_count += 1

    print("-" * 40)
    print(f"Done. Created {created_count} directories, skipped {skipped_count}.")
    
    # Verify existence by listing them
    print("\nVerification of directory tree:")
    for dir_path in dirs_to_create:
        full_path = root_dir / dir_path
        if full_path.exists():
            print(f"  ✓ {dir_path}")
        else:
            print(f"  ✗ {dir_path} (MISSING)")
            return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
