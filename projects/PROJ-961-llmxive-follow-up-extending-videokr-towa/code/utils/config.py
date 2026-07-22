import os
import random
from pathlib import Path
from typing import Any, Dict, Optional, Union

def get_project_root() -> Path:
    """
    Get the project root directory.
    
    Returns:
        Path to the project root.
    """
    return Path(__file__).resolve().parents[2]

def get_path(relative_path: Union[str, Path]) -> Path:
    """
    Get an absolute path relative to the project root.
    
    Args:
        relative_path: Relative path string or Path.
        
    Returns:
        Absolute Path.
    """
    return get_project_root() / relative_path

def ensure_dir(path: Path) -> None:
    """
    Ensure a directory exists.
    
    Args:
        path: Path to the directory.
    """
    path.mkdir(parents=True, exist_ok=True)

def set_seed(seed: int) -> None:
    """
    Set the random seed for reproducibility.
    
    Args:
        seed: Integer seed.
    """
    random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)

def get_config() -> Dict[str, Any]:
    """
    Load configuration from a file.
    
    Returns:
        Configuration dictionary.
    """
    config_path = get_project_root() / "config" / "project_config.json"
    if config_path.exists():
        import json
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}