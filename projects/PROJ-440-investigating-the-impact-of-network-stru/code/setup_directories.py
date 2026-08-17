"""
Setup script for creating the project directory structure.
"""
import os
from pathlib import Path


def setup_directories():
    """
    Create the required directory structure for the project.
    """
    base_dir = Path(__file__).parent.parent
    
    # Define all required directories
    directories = [
        'code',
        'data',
        'data/raw',
        'data/processed',
        'data/analysis',
        'tests',
        'contracts',
        'state'
    ]
    
    for dir_path in directories:
        full_path = base_dir / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {full_path}")
    
    # Create __init__.py in code/
    code_init = base_dir / 'code' / '__init__.py'
    if not code_init.exists():
        code_init.touch()
        print(f"Created: {code_init}")
    
    # Create .gitkeep in data/
    data_gitkeep = base_dir / 'data' / '.gitkeep'
    if not data_gitkeep.exists():
        data_gitkeep.touch()
        print(f"Created: {data_gitkeep}")
    
    print("Directory setup complete.")


if __name__ == '__main__':
    setup_directories()
