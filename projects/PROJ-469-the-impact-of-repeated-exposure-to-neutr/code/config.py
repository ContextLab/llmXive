import os
from pathlib import Path

def ensure_dirs(*paths):
    """
    Ensures that the directories for the given paths exist.
    
    Args:
        *paths: Variable number of Path objects or strings representing file paths.
               The parent directories of these paths will be created if they don't exist.
    """
    for p in paths:
        path_obj = Path(p)
        path_obj.parent.mkdir(parents=True, exist_ok=True)