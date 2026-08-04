"""
Data Directory Setup Module

This module provides utilities to ensure the data directory structure
exists and contains .gitkeep files to preserve empty directories in version control.
"""
import os
import sys
from typing import List, Optional

# Define the required data subdirectories relative to the project root
DATA_SUBDIRS = [
    "data/raw",
    "data/generated",
    "data/results"
]

def ensure_gitkeep(directory: str) -> bool:
    """
    Ensure a directory exists and contains a .gitkeep file.

    Args:
        directory: Path to the directory.

    Returns:
        True if the directory and .gitkeep file were successfully ensured,
        False otherwise.
    """
    try:
        # Create directory if it doesn't exist (including parents)
        os.makedirs(directory, exist_ok=True)
        
        gitkeep_path = os.path.join(directory, ".gitkeep")
        
        # Create .gitkeep if it doesn't exist
        if not os.path.exists(gitkeep_path):
            with open(gitkeep_path, 'w') as f:
                f.write("# Git keep file to preserve directory structure\n")
            return True
        else:
            # Directory and .gitkeep already exist
            return True
    except Exception as e:
        print(f"Error ensuring gitkeep in {directory}: {e}", file=sys.stderr)
        return False

def main(base_path: Optional[str] = None) -> int:
    """
    Main entry point to set up the data directory structure.

    Returns:
        Exit code: 0 on success, 1 on failure.
    """
    # Determine project root (assume script is run from project root or code/ subdirectory)
    # If running from code/, go up one level
    if os.path.basename(os.getcwd()) == "code":
        project_root = os.path.dirname(os.getcwd())
    else:
        project_root = os.getcwd()

    success = True
    for subdir in DATA_SUBDIRS:
        full_path = os.path.join(project_root, subdir)
        if not ensure_gitkeep(full_path):
            success = False
            print(f"Failed to setup: {full_path}", file=sys.stderr)
        else:
            print(f"Ensured: {full_path}")

    if success:
        print("Data directory structure setup complete.")
        return 0
    else:
        print("Data directory setup encountered errors.", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())