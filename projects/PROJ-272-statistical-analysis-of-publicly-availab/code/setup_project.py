"""
Project setup utility for the llmXive statistical analysis pipeline.
Creates the required directory structure as per the implementation plan.
"""
import os
import sys
from pathlib import Path

def create_directory(base_path: str, relative_path: str) -> bool:
    """
    Creates a directory at the specified relative path from the base path.
    
    Args:
        base_path: The root directory of the project.
        relative_path: The relative path to the directory to create.
        
    Returns:
        True if the directory was created or already exists, False otherwise.
    """
    full_path = Path(base_path) / relative_path
    try:
        full_path.mkdir(parents=True, exist_ok=True)
        return True
    except OSError as e:
        print(f"Error creating directory {full_path}: {e}", file=sys.stderr)
        return False

def main() -> int:
    """
    Main function to create the project directory structure.
    
    Returns:
        0 if all directories were created successfully, 1 otherwise.
    """
    # Determine the project root (assuming this script is in code/ or code/setup_project.py)
    # We look for the parent of 'code' or assume current working directory if 'code' is not found
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent if current_file.name == "setup_project.py" else current_file.parent

    # Define the required directory structure relative to project root
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "data/interim",
        "data/results",
        "tests/unit",
        "tests/contract",
        "tests/integration",
        "specs/001-statistical-cognitive-decline/contracts",
    ]

    success = True
    for dir_path in directories:
        if create_directory(project_root, dir_path):
            print(f"Created directory: {project_root / dir_path}")
        else:
            success = False
            print(f"Failed to create directory: {project_root / dir_path}")

    if success:
        print("Project structure setup complete.")
        return 0
    else:
        print("Project structure setup failed.", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
