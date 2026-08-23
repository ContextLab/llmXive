"""
Script to initialize the project data directory structure.
Creates required directories and __init__.py files for data organization.
"""
import os
from pathlib import Path

def setup_data_directories():
    """
    Creates the standard data directory structure for the project.
    Directories created:
      - data/raw/
      - data/processed/
      - data/results/
      - data/config/
      - data/citations/
    
    Also ensures __init__.py files exist in each directory for Python package recognition.
    """
    base_dir = Path(__file__).resolve().parent.parent
    data_root = base_dir / "data"
    
    subdirectories = [
        "raw",
        "processed",
        "results",
        "config",
        "citations"
    ]
    
    print(f"Setting up data directories under: {data_root}")
    
    for subdir_name in subdirectories:
        dir_path = data_root / subdir_name
        dir_path.mkdir(parents=True, exist_ok=True)
        
        init_file = dir_path / "__init__.py"
        if not init_file.exists():
            init_file.write_text(f'"""\n{subdir_name.capitalize()} data storage.\n"""\n')
            print(f"Created: {dir_path} (with __init__.py)")
        else:
            print(f"Exists: {dir_path}")
    
    print("Data directory structure setup complete.")

if __name__ == "__main__":
    setup_data_directories()