import os
import sys
from pathlib import Path

def create_directory(path_str: str) -> bool:
    """
    Creates a directory at the specified path if it does not already exist.
    
    Args:
        path_str: The relative or absolute path to the directory.
        
    Returns:
        True if the directory was created or already exists, False otherwise.
    """
    path = Path(path_str)
    try:
        path.mkdir(parents=True, exist_ok=True)
        return True
    except OSError as e:
        print(f"Error creating directory {path}: {e}", file=sys.stderr)
        return False

def main():
    """
    Main entry point for creating the data/logs directory.
    """
    log_dir = Path("data/logs")
    print(f"Ensuring directory exists: {log_dir}")
    if create_directory(log_dir):
        print(f"Successfully created or verified existence of: {log_dir}")
        return 0
    else:
        print(f"Failed to create directory: {log_dir}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())