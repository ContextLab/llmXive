"""
Project initialization script for PROJ-064.
Creates the standard directory structure required by the llmXive pipeline.
"""
import os
import sys
from pathlib import Path


def initialize_project_structure():
    """
    Creates the complete directory structure for the project.
    
    Structure created under 'projects/PROJ-064-statistical-discrepancies-in-publicly-av/':
    - code/
    - data/raw/
    - data/processed/
    - tests/
    - docs/
    - state/
    - config/
    
    Returns:
        bool: True if successful, False otherwise.
    """
    # Define the base project directory
    base_dir = Path("projects/PROJ-064-statistical-discrepancies-in-publicly-av")
    
    # Define all required subdirectories
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "tests",
        "docs",
        "state",
        "config"
    ]
    
    success = True
    
    for dir_name in directories:
        target_path = base_dir / dir_name
        try:
            target_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {target_path}")
        except OSError as e:
            print(f"Error creating directory {target_path}: {e}")
            success = False
    
    if success:
        print(f"Successfully initialized project structure at {base_dir}")
    else:
        print("Project initialization completed with errors.")
        
    return success


if __name__ == "__main__":
    success = initialize_project_structure()
    sys.exit(0 if success else 1)
