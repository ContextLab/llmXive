import os
import sys
from pathlib import Path
from utils.config import get_project_root, get_path, ensure_dirs_exist

def main():
    """
    Setup the data directory structure for the project.
    Creates data/raw, data/derived, data/logs, data/results under the project root.
    """
    project_root = get_project_root()
    data_path = get_path("data")
    
    # Define required subdirectories
    subdirs = ["raw", "derived", "logs", "results"]
    
    print(f"Ensuring data directory structure at: {data_path}")
    for subdir in subdirs:
        dir_path = data_path / subdir
        ensure_dirs_exist(dir_path)
        print(f"  Created: {dir_path}")
    
    print("Data directory structure setup complete.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
