"""
Project Structure Setup Script.
Creates the required directory tree for the llmXive automated science pipeline.
"""
import os
import sys
from pathlib import Path


def main():
    """Create the standard project directory structure."""
    # Define the root directory (current working directory or specified path)
    root = Path.cwd()

    # Define the required directories relative to the root
    # Based on T001 requirements: code/utils, data/raw, data/processed, data/results,
    # data/metadata, tests/unit, tests/integration, docs
    directories = [
        "code/utils",
        "data/raw",
        "data/processed",
        "data/results",
        "data/metadata",
        "tests/unit",
        "tests/integration",
        "docs",
    ]

    created_count = 0
    skipped_count = 0

    print(f"Setting up project structure in: {root}")

    for dir_path_str in directories:
        dir_path = root / dir_path_str
        try:
            if dir_path.exists():
                print(f"  [SKIP] {dir_path_str} (already exists)")
                skipped_count += 1
            else:
                dir_path.mkdir(parents=True, exist_ok=True)
                print(f"  [OK]   {dir_path_str}")
                created_count += 1
        except PermissionError:
            print(f"  [FAIL] {dir_path_str} (Permission denied)")
            sys.exit(1)
        except Exception as e:
            print(f"  [FAIL] {dir_path_str} ({e})")
            sys.exit(1)

    print(f"\nSetup complete. Created: {created_count}, Skipped: {skipped_count}")
    
    # Verify structure by printing a tree-like representation
    print("\nVerified Directory Structure:")
    for dir_path_str in directories:
        dir_path = root / dir_path_str
        if dir_path.exists():
            print(f"  {dir_path}/")
        else:
            print(f"  {dir_path}/ [MISSING]")
            sys.exit(1)

    return 0


if __name__ == "__main__":
    sys.exit(main())