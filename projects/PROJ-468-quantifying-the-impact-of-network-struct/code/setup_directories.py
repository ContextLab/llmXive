"""
Setup script to create the required directory structure for the project.
Creates data/raw, data/processed, and results directories.
"""
import os
import sys
from pathlib import Path

def create_directories(base_path: Path) -> None:
    """
    Create the necessary directory structure for the project.
    
    Args:
        base_path: The root directory of the project.
    """
    # Define the directories to create
    directories = [
        base_path / "data" / "raw",
        base_path / "data" / "processed",
        base_path / "results",
    ]
    
    created_count = 0
    for directory in directories:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {directory}")
            created_count += 1
        else:
            print(f"Directory already exists: {directory}")
    
    print(f"\nSetup complete. {created_count} new directories created.")

def main() -> int:
    """
    Main entry point for the setup script.
    
    Returns:
        0 on success, 1 on failure.
    """
    # Determine the project root (parent of 'code' directory)
    current_file = Path(__file__).resolve()
    code_dir = current_file.parent
    project_root = code_dir.parent
    
    try:
        create_directories(project_root)
        return 0
    except Exception as e:
        print(f"Error creating directories: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())