"""
Task T002: Create project structure per implementation plan.

Creates the following directories at the repository root:
- code/
- tests/
- data/raw/
- data/processed/
- data/results/
- state/projects/
"""
import os
from pathlib import Path

def create_project_structure():
    """Create the standard project directory structure."""
    # Define the directories to create relative to the project root
    # We assume the script is run from the project root or the path is relative to cwd
    # However, to be robust, we create them relative to the current working directory
    # which should be the project root when run via the quickstart.
    
    base_path = Path.cwd()
    
    directories = [
        base_path / "code",
        base_path / "tests",
        base_path / "data" / "raw",
        base_path / "data" / "processed",
        base_path / "data" / "results",
        base_path / "state" / "projects",
    ]
    
    created_count = 0
    for directory in directories:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {directory}")
            created_count += 1
        else:
            print(f"Directory already exists: {directory}")
    
    return created_count

def main():
    """Entry point for the script."""
    print("Creating project structure...")
    count = create_project_structure()
    print(f"Project structure creation complete. Created {count} new directories.")

if __name__ == "__main__":
    main()
