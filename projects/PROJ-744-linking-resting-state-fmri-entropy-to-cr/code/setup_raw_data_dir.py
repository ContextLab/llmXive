"""
Task T001b: Create directory: `data/raw`

This script ensures the existence of the raw data directory structure
required for storing downloaded HCP fMRI data.
"""
import os
import sys
from pathlib import Path

def create_directory(path_str: str) -> Path:
    """
    Create a directory if it does not exist.
    
    Args:
        path_str: Relative path from project root to the directory.
        
    Returns:
        The Path object of the created (or existing) directory.
    """
    path = Path(path_str)
    path.mkdir(parents=True, exist_ok=True)
    return path

def main():
    """Main entry point for T001b."""
    project_root = Path(__file__).resolve().parent.parent
    target_dir = project_root / "data" / "raw"
    
    print(f"Creating directory: {target_dir}")
    created_dir = create_directory(str(target_dir.relative_to(project_root)))
    
    if created_dir.exists():
        print(f"SUCCESS: Directory '{target_dir}' exists.")
    else:
        print(f"ERROR: Failed to create directory '{target_dir}'.")
        sys.exit(1)

if __name__ == "__main__":
    main()
