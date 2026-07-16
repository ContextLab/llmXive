import os
import sys
from pathlib import Path

def setup_directories():
    """
    Creates the required data directory structure for the project.
    
    Directories created:
    - data/raw: For raw, unprocessed data downloads
    - data/processed: For cleaned and transformed data
    - data/splits: For train/test split definitions (if static)
    - results: For model outputs, metrics, and plots
    
    Returns:
        dict: A mapping of directory names to their absolute Path objects.
    
    Raises:
        OSError: If a directory cannot be created due to permissions or other OS errors.
    """
    base_dir = Path(__file__).resolve().parent.parent
    data_root = base_dir / "data"
    
    directories = {
        "raw": data_root / "raw",
        "processed": data_root / "processed",
        "splits": data_root / "splits",
        "results": base_dir / "results"
    }
    
    for name, path in directories.items():
        try:
            if not path.exists():
                path.mkdir(parents=True, exist_ok=True)
                print(f"Created directory: {path}")
            else:
                print(f"Directory already exists: {path}")
        except OSError as e:
            print(f"Error creating directory {path}: {e}")
            raise e
    
    return directories
