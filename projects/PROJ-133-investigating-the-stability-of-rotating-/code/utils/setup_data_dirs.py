import os
import sys
from pathlib import Path

def create_project_structure() -> None:
    """
    Create the required directory structure for the project.
    
    This function ensures the following directories exist:
    - data/raw
    - data/processed
    - data/aggregated
    - code
    - tests
    - docs
    
    The structure is created relative to the project root.
    """
    # Define the base directory (project root)
    # We assume this script is run from the project root or the project root
    # is the parent of the 'code' directory.
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent
    
    # Define the directories to create
    directories = [
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "data" / "aggregated",
        project_root / "code",
        project_root / "tests",
        project_root / "docs",
        # Ensure subdirectories for tests if needed by other tasks
        project_root / "tests" / "unit",
        project_root / "tests" / "contract",
        project_root / "tests" / "integration",
        # Ensure subdirectories for code if needed
        project_root / "code" / "simulation",
        project_root / "code" / "analysis",
        project_root / "code" / "statistics",
        project_root / "code" / "viz",
        project_root / "code" / "utils",
        project_root / "code" / "models",
        project_root / "code" / "config",
    ]
    
    created_count = 0
    for directory in directories:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            created_count += 1
        # else: directory already exists, no action needed
    
    print(f"Project structure ensured. {created_count} new directories created.")

def main() -> None:
    """Entry point for creating the project structure."""
    create_project_structure()

if __name__ == "__main__":
    main()