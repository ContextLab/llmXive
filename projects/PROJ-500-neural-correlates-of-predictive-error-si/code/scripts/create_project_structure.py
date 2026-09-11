"""
Script to create the initial project directory structure.
Creates: src/, tests/, contracts/, data/, analysis/
"""
import os
import sys
from pathlib import Path

def create_project_structure():
    """Create the standard project directory structure."""
    # Define the directories to create relative to the project root
    directories = [
        "src",
        "tests",
        "contracts",
        "data",
        "analysis",
        # Subdirectories for better organization
        "src/data",
        "src/utils",
        "src/analysis",
        "tests/unit",
        "tests/integration",
        "tests/contract",
        "analysis/results",
        "figures",
        "state",
        "state/projects",
        "docs",
    ]

    project_root = Path(__file__).parent.parent
    
    print(f"Creating project structure in: {project_root}")
    
    created_count = 0
    for dir_path in directories:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created: {full_path}")
            created_count += 1
        else:
            print(f"Already exists: {full_path}")
    
    print(f"\nProject structure creation complete. Created {created_count} new directories.")
    return True

def main():
    """Entry point for the script."""
    try:
        success = create_project_structure()
        if success:
            print("SUCCESS: Project structure created successfully.")
            return 0
        else:
            print("ERROR: Failed to create project structure.")
            return 1
    except Exception as e:
        print(f"ERROR: Unexpected exception during project structure creation: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
