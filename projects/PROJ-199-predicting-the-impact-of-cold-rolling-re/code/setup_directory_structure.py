"""
Script to initialize the top-level directory structure and subdirectories.
This script ensures that all required directories exist for the project.

It creates:
- code/, data/, tests/, docs/ at the root
- data/raw/, data/processed/, data/interim/
- .gitkeep files in each directory to ensure Git tracks them.
"""
import os
from pathlib import Path

def main():
    """Create the project directory structure."""
    root = Path(__file__).resolve().parent.parent
    
    # Define top-level directories
    top_dirs = ['code', 'data', 'tests', 'docs']
    
    # Define subdirectories for data
    data_subdirs = [
        'data/raw',
        'data/processed',
        'data/interim'
    ]
    
    # Create top-level directories
    for dir_name in top_dirs:
        dir_path = root / dir_name
        dir_path.mkdir(exist_ok=True)
        # Create .gitkeep in top-level dirs
        (dir_path / '.gitkeep').touch(exist_ok=True)
        print(f"Created directory: {dir_path}")
    
    # Create data subdirectories
    for dir_path_str in data_subdirs:
        dir_path = root / dir_path_str
        dir_path.mkdir(exist_ok=True)
        # Create .gitkeep in subdirectories
        (dir_path / '.gitkeep').touch(exist_ok=True)
        print(f"Created directory: {dir_path}")
    
    print("Directory structure initialization complete.")

if __name__ == '__main__':
    main()