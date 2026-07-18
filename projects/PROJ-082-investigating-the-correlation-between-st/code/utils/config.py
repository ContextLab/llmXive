"""
Configuration Management Module

Handles seed pinning, path loading, and project root resolution.
"""
import os
import random
from pathlib import Path
from typing import Any, Dict, Optional, Union
import numpy as np

def get_project_root() -> Path:
    """
    Returns the project root directory.
    Assumes the project root is the parent of the 'code' directory.
    """
    current_file = Path(__file__).resolve()
    # Traverse up to find 'code' directory, then go one level up
    for parent in current_file.parents:
        if parent.name == 'code':
            return parent
    # Fallback: assume current directory is root if 'code' not found in path
    return current_file.parent

def set_seed(seed: int = 42) -> None:
    """
    Sets the random seed for reproducibility across numpy, random, and python's hash.
    
    Args:
        seed: Integer seed value.
    """
    random.seed(seed)
    np.random.seed(seed)
    # Note: Python's hash randomization cannot be disabled globally without env vars,
    # but we ensure deterministic behavior for our own random operations.

def get_config_path() -> Path:
    """Returns the path to the main configuration file."""
    return get_project_root() / "config" / "settings.yaml"

def get_output_path(filename: str) -> Path:
    """Returns the full path for a data output file."""
    return get_project_root() / "data" / "derived" / filename

def get_figure_path(filename: str) -> Path:
    """Returns the full path for a figure output file."""
    return get_project_root() / "data" / "figures" / filename

def load_config_from_env(key: str, default: Optional[str] = None) -> Optional[str]:
    """Loads a configuration value from environment variables."""
    return os.getenv(key, default)

def resolve_path(path: Union[str, Path], base: Optional[Path] = None) -> Path:
    """
    Resolves a path relative to a base directory.
    
    Args:
        path: Path string or Path object.
        base: Base directory. Defaults to project root.
        
    Returns:
        Resolved Path object.
    """
    p = Path(path)
    if p.is_absolute():
        return p
    base = base or get_project_root()
    return base / p

def ensure_directory(path: Union[str, Path]) -> Path:
    """
    Ensures the directory for the given path exists.
    
    Args:
        path: Path to a file or directory.
        
    Returns:
        The directory Path.
    """
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p