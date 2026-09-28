"""
Setup Structure Module
Creates the detailed directory structure for the project.
"""
import os
import sys
from pathlib import Path

def create_directories():
    """
    Creates the required directory structure for the project.
    
    Creates:
    - code/data, code/analysis, code/viz, code/utils
    - data/raw, data/processed
    - tests/unit, tests/integration
    """
    # Base path is the project root (parent of the code directory)
    # We assume this script is run from the project root or the code directory
    current_dir = Path(__file__).parent
    project_root = current_dir.parent if current_dir.name == "code" else current_dir

    # Define the directories to create relative to project root
    directories = [
        "code/data",
        "code/analysis",
        "code/viz",
        "code/utils",
        "data/raw",
        "data/processed",
        "tests/unit",
        "tests/integration"
    ]

    created_count = 0
    for dir_path in directories:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")

    print(f"\nTotal directories created: {created_count}")
    return project_root

def main():
    """Main entry point for the setup script."""
    print("Setting up project directory structure...")
    project_root = create_directories()
    print(f"Project root: {project_root}")
    print("Directory structure setup complete.")

if __name__ == "__main__":
    main()