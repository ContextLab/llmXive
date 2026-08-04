"""
Module to setup the data directory structure for the llmXive project.
Creates necessary directories and .gitkeep files to ensure they are tracked by git.
"""
import os
import sys
from typing import List, Optional

# Define the base data directory structure relative to the project root
DATA_DIRS = [
    "data/raw",
    "data/generated",
    "data/results"
]

def ensure_gitkeep(directory: str) -> None:
    """
    Ensure a .gitkeep file exists in the specified directory.
    Creates the directory if it doesn't exist.

    Args:
        directory: Path to the directory.
    """
    os.makedirs(directory, exist_ok=True)
    gitkeep_path = os.path.join(directory, ".gitkeep")
    if not os.path.exists(gitkeep_path):
        with open(gitkeep_path, 'w') as f:
            f.write("# Keep this directory in version control\n")
        print(f"Created: {gitkeep_path}")
    else:
        print(f"Already exists: {gitkeep_path}")

def main(base_path: Optional[str] = None) -> int:
    """
    Main entry point to setup data directories.

    Args:
        base_path: Optional base path to prepend to directory paths.
                  If None, uses current working directory.

    Returns:
        0 on success, 1 on failure.
    """
    if base_path is None:
        base_path = os.getcwd()
    
    print(f"Setting up data directories in: {base_path}")
    
    success = True
    for dir_name in DATA_DIRS:
        full_path = os.path.join(base_path, dir_name)
        try:
            ensure_gitkeep(full_path)
        except Exception as e:
            print(f"ERROR: Failed to setup {full_path}: {e}", file=sys.stderr)
            success = False
    
    if success:
        print("Data directory structure setup complete.")
        return 0
    else:
        print("Data directory setup encountered errors.", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
