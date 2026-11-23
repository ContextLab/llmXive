"""
Script to create required data directories for the project.
Creates: data/raw/, data/processed/, data/synthetic/, data/derivation_logs/
"""
import os
import sys
from pathlib import Path


def create_directory(path: Path) -> bool:
    """
    Create a directory if it does not exist.
    
    Args:
        path: Path object representing the directory to create
        
    Returns:
        True if directory was created or already exists, False otherwise
    """
    try:
        path.mkdir(parents=True, exist_ok=True)
        return True
    except OSError as e:
        print(f"Error creating directory {path}: {e}", file=sys.stderr)
        return False


def main():
    """Create all required data directories."""
    # Define the data directories to create
    data_dirs = [
        "data/raw",
        "data/processed",
        "data/synthetic",
        "data/derivation_logs"
    ]
    
    # Get the project root (parent of code/)
    project_root = Path(__file__).parent.parent
    
    # Create each directory
    success = True
    for dir_name in data_dirs:
        dir_path = project_root / dir_name
        if not create_directory(dir_path):
            success = False
            print(f"Failed to create directory: {dir_path}", file=sys.stderr)
        else:
            print(f"Created directory: {dir_path}")
    
    if not success:
        print("Some directories failed to create.", file=sys.stderr)
        sys.exit(1)
    
    print("All data directories created successfully.")


if __name__ == "__main__":
    main()
