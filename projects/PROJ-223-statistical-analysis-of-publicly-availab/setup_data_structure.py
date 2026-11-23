"""
Setup script to create the required directory structure for the project.
Creates code/, tests/, and data/ directories with subdirectories as specified.
"""
import os
from pathlib import Path

def create_data_directories():
    """Create the data directory structure: raw/, processed/, reports/"""
    base_dir = Path("data")
    subdirs = ["raw", "processed", "reports"]
    
    for subdir in subdirs:
        dir_path = base_dir / subdir
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {dir_path}")
    
    # Create __init__.py files to make them packages
    for subdir in subdirs:
        init_path = base_dir / subdir / "__init__.py"
        init_path.touch()
    
    print(f"Data directory structure created at {base_dir}")

def create_project_structure():
    """Create the main project directories: code/, tests/"""
    dirs = ["code", "tests"]
    
    for dir_name in dirs:
        dir_path = Path(dir_name)
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {dir_path}")
        
        # Create __init__.py
        init_path = dir_path / "__init__.py"
        init_path.touch()
        print(f"Created {init_path}")

if __name__ == "__main__":
    print("Setting up project directory structure...")
    create_project_structure()
    create_data_directories()
    print("Setup complete.")
