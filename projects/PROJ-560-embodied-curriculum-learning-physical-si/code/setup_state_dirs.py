"""
Script to create state directories for the project.
Ensures the state directory structure exists for project PROJ-560.
"""
import os
import sys
from pathlib import Path

def create_directory(path: Path) -> bool:
    """
    Create a directory if it does not exist.
    
    Args:
        path: The Path object representing the directory to create.
        
    Returns:
        True if the directory was created or already exists, False otherwise.
    """
    try:
        path.mkdir(parents=True, exist_ok=True)
        return True
    except OSError as e:
        print(f"Error creating directory {path}: {e}", file=sys.stderr)
        return False

def main():
    """
    Main entry point to create state directories.
    Creates the specific state directory for PROJ-560.
    """
    # Define the project root relative to this script's location
    # Assuming script is in code/ and project root is one level up
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent
    
    state_dir = project_root / "state" / "projects" / "PROJ-560-embodied-curriculum-learning-physical-si"
    
    print(f"Ensuring state directory exists: {state_dir}")
    
    if create_directory(state_dir):
        print(f"Successfully created or verified directory: {state_dir}")
        return 0
    else:
        print(f"Failed to create directory: {state_dir}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())