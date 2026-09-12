"""
Core configuration and directory management for the research pipeline.
"""
import os
from pathlib import Path

def ensure_dirs(dirs: list = None) -> None:
    """
    Ensure that the specified directories exist, creating them if necessary.
    
    Args:
        dirs: List of directory paths (relative or absolute) to ensure exist.
             If None, defaults to standard project directories.
    """
    if dirs is None:
        dirs = [
            "logs",
            "data/raw",
            "data/processed",
            "results",
            "figures",
        ]
    
    for dir_path in dirs:
        path = Path(dir_path)
        path.mkdir(parents=True, exist_ok=True)
