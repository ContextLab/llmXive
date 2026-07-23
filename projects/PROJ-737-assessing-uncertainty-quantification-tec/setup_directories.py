"""
Script to create the required directory structure for the project.
"""
import os
import sys
from pathlib import Path

def main():
    """Create all required directories for the project."""
    project_root = Path(__file__).parent
    
    # Define directory structure
    directories = [
        'data/raw',
        'data/processed',
        'code/models',
        'code/metrics',
        'code/stats',
        'code/utils',
        'results',
        'tests/unit',
        'tests/integration',
        'figures',
        'docs',
    ]
    
    # Create directories
    for dir_path in directories:
        full_path = project_root / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"Created: {full_path}")
    
    # Create __init__.py files in Python packages
    init_files = [
        'code/__init__.py',
        'code/models/__init__.py',
        'code/metrics/__init__.py',
        'code/stats/__init__.py',
        'code/utils/__init__.py',
        'tests/__init__.py',
        'tests/unit/__init__.py',
        'tests/integration/__init__.py',
    ]
    
    for init_file in init_files:
        full_path = project_root / init_file
        if not full_path.exists():
            full_path.touch()
            print(f"Created: {full_path}")
        else:
            print(f"Exists: {full_path}")
    
    print("\nDirectory structure setup complete!")

if __name__ == "__main__":
    main()