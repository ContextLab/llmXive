import os
from pathlib import Path

def setup_data_directories():
    """
    Create the required data directory structure:
    - data/raw/
    - data/processed/
    
    Also ensures the parent 'data' directory exists.
    """
    base_dir = Path(__file__).resolve().parent.parent
    data_dir = base_dir / "data"
    raw_dir = data_dir / "raw"
    processed_dir = data_dir / "processed"

    for directory in [data_dir, raw_dir, processed_dir]:
        directory.mkdir(parents=True, exist_ok=True)
    
    # Create .gitkeep files to ensure directories are tracked by git
    for directory in [data_dir, raw_dir, processed_dir]:
        gitkeep = directory / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.touch()

    return True
