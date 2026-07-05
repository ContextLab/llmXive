"""Script to create the project directory structure."""

import os
import sys
from pathlib import Path

def create_directory_structure():
    """Create all required project directories."""
    base_path = Path(__file__).parent.parent
    
    directories = [
        # Data directories
        base_path / 'data' / 'raw',
        base_path / 'data' / 'processed',
        base_path / 'data' / 'output',
        
        # Code directories
        base_path / 'code' / 'utils',
        base_path / 'code' / 'models',
        base_path / 'code' / 'tests',
        
        # Test directories
        base_path / 'tests' / 'unit',
        base_path / 'tests' / 'integration',
        
        # Specs directories
        base_path / 'specs' / '001-assessing-the-impact-of-sample-size-on-t',
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {directory}")
        
    # Create __init__.py files for Python packages
    init_files = [
        base_path / 'code' / 'utils' / '__init__.py',
        base_path / 'code' / 'models' / '__init__.py',
        base_path / 'code' / 'tests' / '__init__.py',
    ]
    
    for init_file in init_files:
        if not init_file.exists():
            init_file.touch()
            print(f"Created {init_file}")
            
    print("Directory structure creation complete.")
    
if __name__ == '__main__':
    create_directory_structure()