"""
Core utility for directory creation used by setup scripts.
"""
import os
from pathlib import Path

def create_directory(path: Path) -> bool:
    """
    Creates a directory at the specified path if it does not exist.
    
    Args:
        path (Path): The directory path to create.
        
    Returns:
        bool: True if the directory was created or already exists, False on failure.
    """
    try:
        path.mkdir(parents=True, exist_ok=True)
        return True
    except OSError as e:
        print(f"Error creating directory {path}: {e}")
        return False

def main():
    """
    Entry point for direct execution (though typically imported).
    """
    print("setup_directories module loaded.")

if __name__ == "__main__":
    main()
