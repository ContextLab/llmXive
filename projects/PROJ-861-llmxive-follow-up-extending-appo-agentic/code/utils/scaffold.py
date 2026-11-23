import os
import sys
from pathlib import Path

def verify_project_root() -> bool:
    """
    Verifies that the current working directory is the project root.
    Checks for the existence of key project files/directories.
    """
    # Check for common project markers
    markers = ["requirements.txt", "pyproject.toml", "code/", "data/", "tests/"]
    current = Path.cwd()
    
    # Check if we are inside the specific project folder or if the markers exist
    # We assume the script is run from the project root.
    for marker in markers:
        if (current / marker).exists():
            return True
    
    # If not found in CWD, check if we are in a subfolder of the project
    # This is a heuristic. For robustness, we might check for a specific project marker.
    # Given the task description, we just need to verify the root exists.
    # If no markers are found, we assume it's not the root.
    return False

def create_directories():
    """
    Creates the core directory structure for the project.
    """
    base_dir = Path.cwd()
    dirs = [
        "code",
        "data",
        "contracts",
        "data/results",
        "docs",
        "state",
        "tests",
        "src"
    ]
    
    for d in dirs:
        path = base_dir / d
        path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {path}")

def main():
    """
    Main entry point for the scaffold script.
    """
    if not verify_project_root():
        print("Error: Current directory does not appear to be the project root.")
        print("Please run this script from the project root directory.")
        sys.exit(1)
    
    print("Project root verified. Creating directory structure...")
    create_directories()
    print("Directory structure created successfully.")

if __name__ == "__main__":
    main()
