import os
import sys
from pathlib import Path

def create_directory(path: str) -> bool:
    """
    Create a directory at the specified path if it does not exist.
    
    Args:
        path: Relative or absolute path to the directory.
        
    Returns:
        True if directory was created or already exists, False otherwise.
    """
    try:
        dir_path = Path(path)
        dir_path.mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        print(f"Error creating directory {path}: {e}", file=sys.stderr)
        return False

def main():
    """
    Main entry point to create the 'code/' directory.
    """
    target_dir = "code"
    if create_directory(target_dir):
        print(f"Successfully created directory: {target_dir}")
        return 0
    else:
        print(f"Failed to create directory: {target_dir}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())