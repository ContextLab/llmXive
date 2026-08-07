import os
from pathlib import Path
from src.utils.directory_manager import setup_project_directories, initialize_checksums

def setup_directories():
    """
    Convenience function to set up all project directories and initialize checksums.
    """
    print("Setting up project directories...")
    dirs = setup_project_directories()
    print(f"Created/verified {len(dirs)} directories:")
    for d in dirs:
        print(f"  - {d}")
        
    print("\nInitializing checksums...")
    initialize_checksums()
    print("Checksums initialized successfully.")
    return True

if __name__ == "__main__":
    setup_directories()
