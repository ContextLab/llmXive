import os
from pathlib import Path
from config import get_project_root

def setup_data_directories():
    """
    Creates the required data directory structure:
    - data/raw/
    - data/processed/
    - data/final/
    
    Each directory is created with a .gitkeep file to ensure
    the directories are tracked by git even when empty.
    """
    project_root = get_project_root()
    data_root = project_root / "data"
    
    directories = [
        data_root / "raw",
        data_root / "processed",
        data_root / "final"
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        gitkeep_path = directory / ".gitkeep"
        if not gitkeep_path.exists():
            gitkeep_path.write_text("")
        
        print(f"Ensured directory: {directory}")
        
    return True
