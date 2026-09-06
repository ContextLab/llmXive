"""
Script to create the required data directory structure for the project.
Creates data/raw, data/simulated, and data/results directories with .gitkeep files.
"""
import os
import sys
from pathlib import Path


def create_directories():
    """
    Create the required data directory structure.
    
    Creates:
    - data/raw/
    - data/simulated/
    - data/results/
    
    Each directory contains a .gitkeep file to ensure they are tracked by git.
    
    Returns:
        bool: True if all directories were created successfully, False otherwise.
    """
    # Define the base data directory
    base_dir = Path(__file__).parent.parent.parent / "data"
    
    # Define the required subdirectories
    required_dirs = [
        base_dir / "raw",
        base_dir / "simulated",
        base_dir / "results"
    ]
    
    success = True
    
    for dir_path in required_dirs:
        try:
            # Create the directory if it doesn't exist
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
            
            # Create .gitkeep file in each directory
            gitkeep_path = dir_path / ".gitkeep"
            gitkeep_path.touch()
            print(f"Created .gitkeep file: {gitkeep_path}")
            
        except Exception as e:
            print(f"Error creating directory {dir_path}: {e}")
            success = False
    
    if success:
        print("All data directories created successfully.")
    else:
        print("Some directories failed to create.")
    
    return success


def main():
    """
    Main entry point for the script.
    """
    print("Setting up data directory structure...")
    success = create_directories()
    
    if not success:
        sys.exit(1)
    
    print("Data directory setup complete.")


if __name__ == "__main__":
    main()