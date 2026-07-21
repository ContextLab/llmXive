"""
Data Directory Structure Setup Module

This module provides utilities to ensure the required data directory structure
exists and contains .gitkeep files to preserve directory structure in Git.
"""

import os
import sys
from typing import List, Optional

# Define the required data subdirectories relative to the project root
REQUIRED_DATA_DIRS = [
    "data/raw",
    "data/generated",
    "data/results"
]

def ensure_gitkeep(dir_path: str) -> bool:
    """
    Ensure a .gitkeep file exists in the specified directory.

    Args:
        dir_path: Path to the directory

    Returns:
        True if the file was created or already existed, False on error
    """
    gitkeep_path = os.path.join(dir_path, ".gitkeep")
    
    try:
        # Ensure the directory exists first
        os.makedirs(dir_path, exist_ok=True)
        
        # Create .gitkeep if it doesn't exist
        if not os.path.exists(gitkeep_path):
            with open(gitkeep_path, 'w') as f:
                f.write("# Keep this directory in version control\n")
            return True
        return True
    except Exception as e:
        print(f"Error ensuring .gitkeep in {dir_path}: {e}", file=sys.stderr)
        return False


def main() -> int:
    """
    Main entry point for setting up data directory structure.

    Returns:
        0 on success, 1 on failure
    """
    # Get project root (assuming this script is in code/ directory)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    
    success = True
    
    for data_dir in REQUIRED_DATA_DIRS:
        full_path = os.path.join(project_root, data_dir)
        
        print(f"Ensuring directory: {full_path}")
        if not ensure_gitkeep(full_path):
            success = False
            print(f"Failed to create .gitkeep in {full_path}")
    
    if success:
        print("Data directory structure setup complete.")
        return 0
    else:
        print("Data directory structure setup failed.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
