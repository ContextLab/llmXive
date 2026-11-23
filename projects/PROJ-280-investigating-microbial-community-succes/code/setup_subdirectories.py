"""
Script to create the required subdirectory structure for the project.
This satisfies task T001b.
"""
import os
from pathlib import Path

def create_subdirectories():
    """
    Creates the following subdirectories relative to the project root:
    - data/raw
    - data/processed
    - data/config
    - tests/unit
    - tests/contract
    - tests/integration
    - state/projects
    """
    # Determine the project root based on the expected structure
    # We assume this script is run from the project root or the root is the parent of 'code'
    script_path = Path(__file__).resolve()
    project_root = script_path.parent

    # Define the subdirectories to create
    subdirs = [
        "data/raw",
        "data/processed",
        "data/config",
        "tests/unit",
        "tests/contract",
        "tests/integration",
        "state/projects",
    ]

    created_count = 0
    for subdir in subdirs:
        target_path = project_root / subdir
        if not target_path.exists():
            target_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {target_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {target_path}")

    print(f"Setup complete. {created_count} new directories created.")
    return True

if __name__ == "__main__":
    success = create_subdirectories()
    if not success:
        exit(1)