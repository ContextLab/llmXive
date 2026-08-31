"""
Script to setup the data directory structure for the BMG Shear Modulus project.
Creates raw/, processed/, and artifacts/ subdirectories under data/.
"""
import os
from pathlib import Path

# Import from the existing utils module as per API surface
from utils.config import get_paths, ensure_directories


def setup_data_structure():
    """
    Creates the required directory structure for data storage.
    Specifically creates:
    - data/raw/
    - data/processed/
    - data/artifacts/
    """
    # Get the project root paths using the existing config utility
    paths = get_paths()
    data_root = paths.get('data_root')
    
    if not data_root:
        # Fallback if config doesn't have it, though it should based on T005
        data_root = Path.cwd() / 'data'
    
    data_path = Path(data_root)
    
    # Define the required subdirectories
    subdirs = [
        'raw',
        'processed',
        'artifacts'
    ]
    
    # Ensure the directories exist
    ensure_directories(data_path, subdirs)
    
    # Create a .gitkeep file in each to ensure they are tracked by git
    for subdir in subdirs:
        dir_path = data_path / subdir
        gitkeep_path = dir_path / '.gitkeep'
        if not gitkeep_path.exists():
            gitkeep_path.touch()
            print(f"Created: {gitkeep_path}")
    
    print(f"Data directory structure created at: {data_path}")
    return True


def main():
    """Entry point for the script."""
    try:
        setup_data_structure()
        print("Data directory setup completed successfully.")
    except Exception as e:
        print(f"Error setting up data directories: {e}")
        raise e


if __name__ == "__main__":
    main()
