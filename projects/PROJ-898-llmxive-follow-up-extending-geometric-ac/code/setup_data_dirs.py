import os
import sys
from typing import List, Optional

def ensure_gitkeep(directory: str) -> None:
    """
    Ensures that the specified directory exists and contains a .gitkeep file.
    If the directory does not exist, it is created.
    If the .gitkeep file does not exist, it is created as an empty file.

    Args:
        directory (str): Path to the directory.
    """
    os.makedirs(directory, exist_ok=True)
    gitkeep_path = os.path.join(directory, ".gitkeep")
    if not os.path.exists(gitkeep_path):
        with open(gitkeep_path, "w") as f:
            f.write("")

def main() -> int:
    """
    Main entry point for creating data subdirectories and .gitkeep files.
    Creates the following directories under 'data/':
        - data/raw
        - data/generated
        - data/results
    And ensures each contains a .gitkeep file.

    Returns:
        int: Exit code (0 for success, 1 for failure).
    """
    data_root = "data"
    subdirs = ["raw", "generated", "results"]
    full_paths = [os.path.join(data_root, subdir) for subdir in subdirs]

    try:
        for path in full_paths:
            ensure_gitkeep(path)
        return 0
    except Exception as e:
        print(f"Error creating data directories or .gitkeep files: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
