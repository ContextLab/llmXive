"""
Script to create the project directory structure for the llmXive research pipeline.
This script ensures all required directories exist before other tasks begin.
"""
import os
from pathlib import Path

def main():
    """Create the standard project directory structure."""
    # Define the base project root (assuming this script is at the root or code/)
    # The task requires paths relative to project root: code/, specs/, etc.
    # Since this file is in code/, we go up one level to find the project root.
    project_root = Path(__file__).resolve().parent.parent

    # Define the directories to create relative to project_root
    dirs_to_create = [
        "code",
        "code/src",
        "code/tests",
        "code/data/raw",
        "code/data/processed",
        "code/data/results",
        "specs/001-code-complexity-bug-prediction",
    ]

    created_count = 0
    for dir_path in dirs_to_create:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")

    print(f"\nSetup complete. {created_count} new directories created.")
    print(f"Project root: {project_root}")

if __name__ == "__main__":
    main()
