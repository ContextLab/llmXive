import os
import random
from pathlib import Path
from typing import Any, Dict

# Project root path
_PROJECT_ROOT: Path = None

def get_project_root() -> Path:
    """Get the project root directory."""
    global _PROJECT_ROOT
    if _PROJECT_ROOT is None:
        # Determine project root by looking for .git or specific files
        current = Path.cwd()
        while current != current.parent:
            if (current / ".git").exists() or (current / "tasks.md").exists():
                _PROJECT_ROOT = current
                return _PROJECT_ROOT
            current = current.parent
        # Fallback to current directory if no project root found
        _PROJECT_ROOT = Path.cwd()
        return _PROJECT_ROOT
    return _PROJECT_ROOT

def set_project_root(path: Path) -> None:
    """Set the project root directory."""
    global _PROJECT_ROOT
    _PROJECT_ROOT = path

def get_path(relative_path: str) -> Path:
    """
    Get an absolute path relative to the project root.
    
    Args:
        relative_path: Path relative to project root
        
    Returns:
        Absolute Path object
    """
    root = get_project_root()
    return root / relative_path

def ensure_dirs(paths: list) -> None:
    """
    Ensure all directories in the list exist.
    
    Args:
        paths: List of Path objects to ensure exist
    """
    for path in paths:
        path.mkdir(parents=True, exist_ok=True)

def set_seed(seed: int = 42) -> None:
    """
    Set random seeds for reproducibility.
    
    Args:
        seed: Random seed value
    """
    random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)
    
    # If numpy is available, set its seed too
    try:
        import numpy as np
        np.random.seed(seed)
    except ImportError:
        pass
