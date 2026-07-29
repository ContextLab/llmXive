"""
Setup script to create required project directories.
Creates 'code', 'artifacts', and 'tests' directories if they do not exist.
"""
import os
import sys
from config import ensure_directories

def main():
    """Main entry point for directory setup."""
    # Define the directories to create relative to project root
    # The config module's ensure_directories handles the creation logic
    # based on the paths defined in the Config class.
    
    # We explicitly ensure these top-level directories exist.
    # Note: ensure_directories in config.py likely creates the full tree
    # (data/raw, data/processed, etc.), but we ensure the root folders exist too.
    
    required_dirs = [
        "code",
        "artifacts",
        "tests"
    ]
    
    for dir_path in required_dirs:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
            print(f"Created directory: {dir_path}")
        else:
            print(f"Directory already exists: {dir_path}")
    
    # Also ensure the subdirectories defined in config are present
    # (T001a creates data subdirs, but we ensure the full tree via config)
    ensure_directories()

    print("Directory setup complete.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
