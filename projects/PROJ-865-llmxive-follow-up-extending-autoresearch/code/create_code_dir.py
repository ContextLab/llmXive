"""
T001a: Create directory `code/` at repository root.

This script ensures the `code/` directory exists at the repository root.
It is idempotent and safe to run multiple times.
"""
import os
import sys
from pathlib import Path

def main():
    # Determine repository root (assuming script is run from root or relative to it)
    # We target the absolute path relative to the current working directory
    repo_root = Path.cwd()
    target_dir = repo_root / "code"

    if target_dir.exists():
        if target_dir.is_dir():
            print(f"Directory '{target_dir}' already exists.")
            return 0
        else:
            print(f"Error: '{target_dir}' exists but is not a directory.")
            return 1

    try:
        target_dir.mkdir(parents=True, exist_ok=True)
        print(f"Successfully created directory: {target_dir}")
        return 0
    except PermissionError:
        print(f"Error: Permission denied when creating '{target_dir}'.")
        return 1
    except Exception as e:
        print(f"Error creating directory '{target_dir}': {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())