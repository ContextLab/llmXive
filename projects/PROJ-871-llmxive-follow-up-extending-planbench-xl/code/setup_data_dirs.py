import os
import sys
from pathlib import Path
from utils.config import get_project_root, get_path, ensure_dirs_exist

def main():
    """
    Setup the data directory structure for the project.
    Creates: data/raw, data/derived, data/logs, data/results
    """
    project_root = get_project_root()
    data_root = project_root / "data"
    
    # Define required subdirectories
    required_dirs = [
        "raw",
        "derived",
        "logs",
        "results"
    ]
    
    # Create directories
    for dir_name in required_dirs:
        dir_path = data_root / dir_name
        ensure_dirs_exist(dir_path)
        print(f"Created directory: {dir_path}")
    
    print(f"Data directory structure initialized at: {data_root}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
