import os
from pathlib import Path
from typing import List

def create_directories(base_path: Path, directories: List[str]) -> None:
    """
    Create a list of directories relative to base_path.
    Raises FileNotFoundError if a directory cannot be created.
    """
    for dir_name in directories:
        dir_path = base_path / dir_name
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            if not dir_path.is_dir():
                raise FileNotFoundError(f"Failed to create directory: {dir_path}")
        except OSError as e:
            raise FileNotFoundError(f"Error creating directory {dir_path}: {e}")

def main() -> None:
    """
    Main entry point for setting up the project directory structure.
    Creates the required directories under the project root.
    """
    project_root = Path(__file__).resolve().parent.parent
    
    # Define required directory structure relative to project root
    required_dirs = [
        "data",
        "data/raw",
        "data/processed",
        "state",
        "tests",
        "tests/contract",
        "tests/unit",
        "tests/integration",
        "docs",
        "code",
        "code/utils"
    ]
    
    print(f"Creating directories in {project_root}...")
    create_directories(project_root, required_dirs)
    print("Directory structure created successfully.")
