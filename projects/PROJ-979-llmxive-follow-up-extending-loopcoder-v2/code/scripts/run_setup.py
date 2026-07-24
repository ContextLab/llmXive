#!/usr/bin/env python3
"""
T001: Initialize project directory structure.

Creates the following directories relative to the project root:
- data/raw, data/processed
- code/src, code/tests, code/notebooks, code/scripts, code/config
- paper
- state
- contracts

Exits with code 0 only if all directories exist after execution.
"""
import os
import sys
from pathlib import Path

def create_directory_structure(root: Path) -> None:
    """Create all required project directories."""
    directories = [
        "data/raw",
        "data/processed",
        "code/src",
        "code/tests",
        "code/notebooks",
        "code/scripts",
        "code/config",
        "paper",
        "state",
        "contracts",
    ]

    for dir_path in directories:
        full_path = root / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"Created: {full_path}")

def verify_directory_structure(root: Path) -> bool:
    """Verify that all required directories exist."""
    directories = [
        "data/raw",
        "data/processed",
        "code/src",
        "code/tests",
        "code/notebooks",
        "code/scripts",
        "code/config",
        "paper",
        "state",
        "contracts",
    ]

    all_exist = True
    for dir_path in directories:
        full_path = root / dir_path
        if not full_path.exists():
            print(f"ERROR: Directory missing: {full_path}")
            all_exist = False
        elif not full_path.is_dir():
            print(f"ERROR: Path exists but is not a directory: {full_path}")
            all_exist = False
        else:
            print(f"Verified: {full_path}")

    return all_exist

def main() -> int:
    """Main entry point for directory setup."""
    # Determine project root (parent of 'code' directory)
    script_dir = Path(__file__).resolve().parent
    code_dir = script_dir
    project_root = code_dir.parent

    print(f"Project root detected at: {project_root}")

    # Create directories
    print("Creating directory structure...")
    create_directory_structure(project_root)

    # Verify
    print("Verifying directory structure...")
    if verify_directory_structure(project_root):
        print("SUCCESS: All directories created and verified.")
        return 0
    else:
        print("FAILURE: Some directories are missing or invalid.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
