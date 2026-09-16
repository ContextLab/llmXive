import os
import sys
from typing import List

# Directories required for the project data pipeline
DATA_DIRS: List[str] = [
    "data/raw/synthetic_graphs",
    "data/processed",
    "data/interim",
    "figures",
    "logs",
]

def create_directories(base_path: str = ".") -> None:
    """
    Creates the required directory structure for the project.
    
    Args:
        base_path: The root directory where data/ will be created.
    """
    for dir_name in DATA_DIRS:
        full_path = os.path.join(base_path, dir_name)
        if not os.path.exists(full_path):
            os.makedirs(full_path)
            print(f"Created directory: {full_path}")
        else:
            # Ensure it is actually a directory, not a file
            if not os.path.isdir(full_path):
                raise RuntimeError(f"Path exists but is not a directory: {full_path}")

def main() -> None:
    """Entry point for script execution."""
    print("Initializing data directory structure...")
    create_directories(".")
    print("Data directory structure ready.")

if __name__ == "__main__":
    main()
