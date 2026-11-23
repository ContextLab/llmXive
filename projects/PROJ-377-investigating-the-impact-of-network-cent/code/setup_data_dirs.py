"""
Setup script to create the required data directory structure.
This script ensures that the data/ directory and its subdirectories
(raw/, processed/, artifacts/) exist for the project.
"""
import os
from pathlib import Path

def setup_data_directories():
    """
    Creates the data directory structure required for the project.
    
    Creates the following directories relative to the project root:
    - data/
    - data/raw/
    - data/processed/
    - data/artifacts/
    
    Returns:
        bool: True if all directories were created successfully, False otherwise.
    """
    project_root = Path(__file__).resolve().parent.parent
    data_root = project_root / "data"
    
    directories = [
        data_root,
        data_root / "raw",
        data_root / "processed",
        data_root / "artifacts"
    ]
    
    success = True
    for directory in directories:
        try:
            directory.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {directory}")
        except OSError as e:
            print(f"Error creating directory {directory}: {e}")
            success = False
    
    return success

if __name__ == "__main__":
    success = setup_data_directories()
    if success:
        print("Data directory structure setup completed successfully.")
    else:
        print("Data directory structure setup completed with errors.")
        exit(1)