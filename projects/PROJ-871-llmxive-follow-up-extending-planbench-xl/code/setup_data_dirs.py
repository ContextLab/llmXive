"""
Script to set up the data directory structure for the project.
Creates: data/raw, data/derived, data/logs, data/results
"""
import os
import sys
from pathlib import Path

# Add parent directory to path to allow imports from utils if needed
# though this script primarily uses stdlib
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.config import get_project_root, get_path, ensure_dirs_exist

def main():
    """
    Main entry point to create the data directory structure.
    """
    project_root = get_project_root()
    data_dir = project_root / "data"
    
    # Define required subdirectories
    required_dirs = [
        "raw",
        "derived",
        "logs",
        "results"
    ]
    
    # Create directories
    created_count = 0
    for dir_name in required_dirs:
        dir_path = data_dir / dir_name
        if ensure_dirs_exist(dir_path):
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            # Directory might already exist
            if dir_path.exists():
                print(f"Directory already exists: {dir_path}")
            else:
                print(f"Failed to create directory: {dir_path}")
    
    print(f"\nData directory setup complete. Created/Verified {created_count} directories.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
