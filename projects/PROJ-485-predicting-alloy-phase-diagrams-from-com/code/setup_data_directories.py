import os
import sys
from typing import List

# Define the required data directory structure relative to the project root
DATA_DIRECTORIES = [
    "data/raw",
    "data/processed",
    "data/artifacts"
]

def create_directories(base_path: str = None) -> List[str]:
    """
    Creates the required data directories if they do not exist.
    
    Args:
        base_path: Optional base path. If None, uses the current working directory.
        
    Returns:
        List of paths to the created directories.
    """
    if base_path is None:
        base_path = os.getcwd()
        
    created_paths = []
    
    for dir_name in DATA_DIRECTORIES:
        full_path = os.path.join(base_path, dir_name)
        if not os.path.exists(full_path):
            os.makedirs(full_path, exist_ok=True)
            created_paths.append(full_path)
        else:
            created_paths.append(full_path)
            
    return created_paths

def main():
    """
    Entry point for creating data directories.
    """
    print("Creating data directories...")
    paths = create_directories()
    for p in paths:
        print(f"  - {p}")
    print("Data directory structure ready.")

if __name__ == "__main__":
    main()