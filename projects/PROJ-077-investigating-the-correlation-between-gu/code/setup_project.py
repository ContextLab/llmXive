import os
import sys
from pathlib import Path
from config import ensure_directories

def main():
    """
    Initialize project directory structure.
    Creates: data/raw, data/processed, code, tests
    """
    print("Initializing project directory structure...")
    
    # Define required directories relative to project root
    required_dirs = [
        "data/raw",
        "data/processed",
        "code",
        "tests"
    ]
    
    # Create directories using ensure_directories from config
    ensure_directories(required_dirs)
    
    # Verify all directories exist
    all_exist = True
    for dir_path in required_dirs:
        if not os.path.isdir(dir_path):
            print(f"ERROR: Directory {dir_path} was not created successfully")
            all_exist = False
    
    if all_exist:
        print("Directories created successfully")
        return 0
    else:
        print("Failed to create some directories")
        return 1

if __name__ == "__main__":
    sys.exit(main())
