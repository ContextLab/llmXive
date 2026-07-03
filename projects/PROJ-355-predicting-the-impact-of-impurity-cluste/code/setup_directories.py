import os
import sys
from pathlib import Path

# Import helper functions from the sibling module
from setup_project import ensure_directory, create_gitkeep

def setup_directories() -> None:
    """
    Initialize the project directory structure for PROJ-355.
    
    Creates the following structure idempotently:
    projects/PROJ-355-predicting-the-impact-of-impurity-cluste/
    ├── code/
    ├── data/
    │   ├── raw/
    │   └── processed/
    ├── results/
    ├── tests/
    │   ├── unit/
    │   └── integration/
    └── .gitkeep (in each leaf directory to ensure git tracking)
    """
    # Define the project root relative to the current working directory
    # The task specifies the path relative to the project root, so we assume
    # the script is run from the root of the repository or the parent of 'projects'.
    # We construct the path dynamically to ensure it lands in the correct spot.
    
    project_root_name = "projects/PROJ-355-predicting-the-impact-of-impurity-cluste"
    base_path = Path(project_root_name)
    
    # Define the required subdirectories relative to the project root
    subdirs = [
        "code",
        "data/raw",
        "data/processed",
        "results",
        "tests/unit",
        "tests/integration"
    ]
    
    print(f"Initializing project structure at: {base_path.absolute()}")
    
    for subdir in subdirs:
        full_path = base_path / subdir
        ensure_directory(full_path)
        create_gitkeep(full_path)
        print(f"  Created: {full_path}")
    
    print("Project structure initialization complete.")

def main() -> None:
    """
    Entry point for running this script directly: python code/setup_directories.py
    """
    setup_directories()

if __name__ == "__main__":
    main()
