import os
import sys
from pathlib import Path
from typing import List

def create_directories(base_path: Path, directories: List[str]) -> None:
    """
    Create a list of directories under the given base path.
    Creates parent directories as needed.
    """
    for dir_name in directories:
        dir_path = base_path / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {dir_path}")

def create_init_files(base_path: Path, directories: List[str]) -> None:
    """
    Create __init__.py files in the specified directories to make them Python packages.
    """
    for dir_name in directories:
        dir_path = base_path / dir_name
        init_file = dir_path / "__init__.py"
        if not init_file.exists():
            init_file.touch()
            print(f"Created __init__.py in: {dir_path}")

def main() -> None:
    """
    Main entry point to set up the project directory structure.
    Creates reports/ directory and initializes it as a package.
    """
    # Define the project root (current working directory or explicit path)
    project_root = Path.cwd()

    # Directories to create
    # Based on T001e: Create 'reports/' directory for final outputs
    directories_to_create = ["reports"]

    print(f"Setting up directories in: {project_root}")

    # Create directories
    create_directories(project_root, directories_to_create)

    # Create __init__.py for reports to make it a package (optional but good practice)
    create_init_files(project_root, directories_to_create)

    print("Directory setup complete.")

if __name__ == "__main__":
    main()
