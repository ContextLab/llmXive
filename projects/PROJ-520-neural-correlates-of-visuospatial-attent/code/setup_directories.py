"""
Setup script to create the required data directory structure.
Ensures data/raw and data/processed directories exist for downstream tasks (T005+).
"""
import os
import sys
from pathlib import Path

def create_directories(base_path: Path) -> bool:
    """
    Create the required directory structure for the project.
    
    Args:
        base_path: The root path where directories should be created.
        
    Returns:
        True if all directories were created successfully, False otherwise.
    """
    directories = [
        base_path / "data" / "raw",
        base_path / "data" / "processed",
    ]
    
    success = True
    for dir_path in directories:
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
        except OSError as e:
            print(f"Error creating directory {dir_path}: {e}", file=sys.stderr)
            success = False
    
    return success

def main() -> int:
    """
    Main entry point for the directory setup script.
    
    Returns:
        Exit code: 0 for success, 1 for failure.
    """
    # Determine the project root (parent of 'code' directory)
    current_file = Path(__file__).resolve()
    code_dir = current_file.parent
    project_root = code_dir.parent
    
    print(f"Project root detected at: {project_root}")
    
    if create_directories(project_root):
        print("Directory structure setup complete.")
        return 0
    else:
        print("Directory structure setup failed.", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
