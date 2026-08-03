"""
Setup data directory structure for the llmXive project.

This module creates the required directory hierarchy under `data/`
and places `.gitkeep` files to ensure they are tracked by git.
"""
import os
import sys
from typing import List, Optional

def ensure_gitkeep(directory: str) -> None:
    """
    Ensure a directory exists and contains a .gitkeep file.
    
    Args:
        directory: Path to the directory to ensure.
    
    Raises:
        OSError: If the directory cannot be created or written to.
    """
    os.makedirs(directory, exist_ok=True)
    gitkeep_path = os.path.join(directory, ".gitkeep")
    
    if not os.path.exists(gitkeep_path):
        with open(gitkeep_path, 'w') as f:
            f.write("# This file ensures the directory is tracked by git.\n")
        print(f"Created: {gitkeep_path}")
    else:
        print(f"Already exists: {gitkeep_path}")

def main() -> int:
    """
    Main entry point to set up the data directory structure.
    
    Creates the following directories under the project root:
    - data/raw
    - data/generated
    - data/results
    
    Returns:
        int: Exit code (0 for success, 1 for failure).
    """
    # Define the required data directories relative to the project root
    data_dirs = [
        "data/raw",
        "data/generated",
        "data/results"
    ]
    
    # Determine project root (assuming this script is in code/)
    # We traverse up one level to get the root
    current_file_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_file_dir)
    
    print(f"Setting up data directories in: {project_root}")
    
    success = True
    for rel_dir in data_dirs:
        full_path = os.path.join(project_root, rel_dir)
        try:
            ensure_gitkeep(full_path)
        except OSError as e:
            print(f"Error creating directory {full_path}: {e}", file=sys.stderr)
            success = False
    
    if success:
        print("Data directory structure setup complete.")
        return 0
    else:
        print("Data directory structure setup failed.", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
