"""
Directory creation utility for the project.
Ensures the existence of the `code` and `code/utils` directories.
"""
import os
import sys
from pathlib import Path
from typing import List

def ensure_directories() -> List[str]:
    """
    Creates the required project directories if they do not exist.
    Specifically targets `code` and `code/utils` for this task.

    Returns:
        List[str]: A list of paths that were created or verified.
    """
    base_path = Path(__file__).resolve().parent.parent
    dirs_to_create = [
        base_path / "code",
        base_path / "code" / "utils"
    ]

    created_or_verified = []
    for dir_path in dirs_to_create:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            created_or_verified.append(str(dir_path))
        else:
            created_or_verified.append(str(dir_path))
    
    return created_or_verified

def main():
    """
    Entry point for the script. Creates directories and logs the result.
    """
    print("Initializing directory structure for T001b...")
    created_paths = ensure_directories()
    
    if not created_paths:
        print("All required directories already exist.")
    else:
        print(f"Created directories: {created_paths}")
    
    print("T001b: Directories 'code' and 'code/utils' are ready.")

if __name__ == "__main__":
    main()
