import os
import sys
from pathlib import Path

def create_project_structure():
    """
    Creates the required directory tree for the project.
    Implements T001a: Create project structure.
    """
    base_dirs = [
        "code",
        "code/utils",
        "tests",
        "data/raw",
        "data/processed",
        "data/synthetic",
        "models",
        "docs",
        "docs/contracts",
        "state/projects"
    ]

    for dir_path in base_dirs:
        path = Path(dir_path)
        if not path.exists():
            path.mkdir(parents=True)
            print(f"Created directory: {dir_path}")
        else:
            print(f"Directory already exists: {dir_path}")

def main():
    create_project_structure()
    print("Project structure initialization complete.")

if __name__ == "__main__":
    main()