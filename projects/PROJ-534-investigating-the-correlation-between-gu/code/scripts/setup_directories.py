"""
Script to create the required project directory structure.
This implements Task T001a: Create project directory structure.
"""
import os
from pathlib import Path

def main():
    """Create the standard project directory structure."""
    # Define the root directory relative to this script's location
    # The script is in code/scripts/, so root is code/
    script_dir = Path(__file__).resolve().parent
    root_dir = script_dir.parent

    # Define the required directories
    directories = [
        "src",
        "tests",
        "data/raw",
        "data/processed",
        "data/results",
        "specs",
        "contracts",
        "logs",
        "figures",
    ]

    created_count = 0
    for dir_name in directories:
        dir_path = root_dir / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path.relative_to(root_dir)}")
            created_count += 1
        else:
            print(f"Directory already exists: {dir_path.relative_to(root_dir)}")

    print(f"\nSetup complete. {created_count} new directories created.")
    print(f"Root directory: {root_dir}")

if __name__ == "__main__":
    main()