import os
import random
from pathlib import Path
from typing import Any, Dict, Optional, Union
import numpy as np

def get_project_root() -> Path:
    """
    Get the project root directory.
    Assumes the project root is two levels up from this file.
    """
    return Path(__file__).resolve().parent.parent.parent

def set_seed(seed: int = 42):
    """
    Set random seeds for reproducibility.
    
    Args:
        seed: Integer seed value.
    """
    random.seed(seed)
    np.random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)

def get_config_path() -> Path:
    """Get the path to the configuration file."""
    return get_project_root() / "config" / "settings.yaml"

def get_output_path(filename: str) -> Path:
    """
    Get the full path for an output file in the data/derived directory.
    
    Args:
        filename: Name of the output file.
    
    Returns:
        Full path to the output file.
    """
    return get_project_root() / "data" / "derived" / filename

def get_figure_path(filename: str) -> Path:
    """
    Get the full path for a figure file in the figures/ directory.
    
    Args:
        filename: Name of the figure file.
    
    Returns:
        Full path to the figure file.
    """
    return get_project_root() / "figures" / filename

def load_config_from_env(key: str, default: Optional[str] = None) -> Optional[str]:
    """
    Load a configuration value from an environment variable.
    
    Args:
        key: Environment variable name.
        default: Default value if key is not found.
    
    Returns:
        Value from environment or default.
    """
    return os.environ.get(key, default)

def resolve_path(path_str: Union[str, Path], base: Optional[Path] = None) -> Path:
    """
    Resolve a path relative to a base directory.
    
    Args:
        path_str: Path string or Path object.
        base: Base directory. Defaults to project root.
    
    Returns:
        Resolved absolute Path.
    """
    if base is None:
        base = get_project_root()
    
    path = Path(path_str)
    if not path.is_absolute():
        path = base / path
    
    return path.resolve()

def ensure_directory(path: Union[str, Path]):
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        path: Directory path.
    """
    dir_path = resolve_path(path)
    dir_path.mkdir(parents=True, exist_ok=True)
