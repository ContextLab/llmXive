import os
from pathlib import Path
from typing import List
from src.utils.config import get_path, ensure_dirs
from src.utils.checksums import update_checksums_for_project

def setup_project_directories() -> List[Path]:
    """
    Creates the required directory structure for the project.
    Returns a list of created directory paths.
    """
    created_dirs = []
    
    # Define the directories to create based on task requirements
    # These are relative to the project root
    required_dirs = [
        "data",
        "data/raw",
        "data/processed",
        "results",
        "specs",
        "state",
        "state/projects"
    ]
    
    for dir_path in required_dirs:
        full_path = get_path(dir_path)
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(full_path)
        else:
            created_dirs.append(full_path)
            
    return created_dirs

def initialize_checksums() -> None:
    """
    Initializes the checksum state file for the project.
    This satisfies Constitution Principle III and V by recording
    the state of the data directories.
    """
    # Ensure the state directory exists first
    state_dir = get_path("state/projects")
    state_dir.mkdir(parents=True, exist_ok=True)
    
    # Update checksums for the project, which will create the state file
    # if it doesn't exist, or update it if it does
    update_checksums_for_project()

def main() -> None:
    """
    Main entry point for directory setup and checksum initialization.
    """
    print("Setting up project directories...")
    dirs = setup_project_directories()
    print(f"Created/verified {len(dirs)} directories:")
    for d in dirs:
        print(f"  - {d}")
        
    print("\nInitializing checksums...")
    initialize_checksums()
    print("Checksums initialized successfully.")
