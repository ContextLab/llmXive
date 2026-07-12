import os
from pathlib import Path

def create_data_structure(base_path: str = None) -> None:
    """
    Wrapper to create the data directory structure specifically.
    Can be called independently or via the main setup script.
    
    Args:
        base_path: Optional override for the base path. Defaults to project root.
    """
    if base_path is None:
        # Default to current directory if not specified
        base_path = Path.cwd()
    else:
        base_path = Path(base_path)
    
    data_dirs = [
        "data/raw",
        "data/processed",
        "data/embeddings",
        "data/cache"
    ]
    
    for dir_path in data_dirs:
        full_path = base_path / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        (full_path / ".gitkeep").touch()
    
    print(f"Data structure created at: {base_path}")