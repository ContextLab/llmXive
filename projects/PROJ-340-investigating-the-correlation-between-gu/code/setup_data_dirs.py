"""
Setup script to create the required data directory structure.
"""
import os
from pathlib import Path

def setup_data_directories():
    """
    Creates the required directory structure for the project data.
    
    Creates:
    - data/raw/
    - data/processed/
    - data/results/
    - data/config/
    - data/citations/
    
    And ensures data/config/__init__.py exists.
    """
    base_dir = Path(__file__).resolve().parent.parent
    data_dir = base_dir / "data"
    
    subdirs = [
        "raw",
        "processed",
        "results",
        "config",
        "citations"
    ]
    
    for subdir in subdirs:
        dir_path = data_dir / subdir
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {dir_path}")
    
    # Ensure __init__.py exists in data/config
    config_init = data_dir / "config" / "__init__.py"
    if not config_init.exists():
        config_init.write_text('"""\\nConfiguration files storage.\\n"""\\n')
        print(f"Created file: {config_init}")
    else:
        print(f"File already exists: {config_init}")
    
    # Create __init__.py in data root if missing
    data_init = data_dir / "__init__.py"
    if not data_init.exists():
        data_init.write_text('"""\\nProject data storage.\\n"""\\n')
        print(f"Created file: {data_init}")
    
    return data_dir

if __name__ == "__main__":
    setup_data_directories()
