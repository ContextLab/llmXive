"""
Utility functions for ingestion tasks.
"""
import os
from pathlib import Path

def ensure_dir(file_path: Path) -> None:
    """
    Ensure the directory for the given file path exists.
    
    Args:
        file_path: Path to the file (directory will be created if missing).
    """
    dir_path = file_path.parent
    if dir_path and not dir_path.exists():
        os.makedirs(dir_path, exist_ok=True)
