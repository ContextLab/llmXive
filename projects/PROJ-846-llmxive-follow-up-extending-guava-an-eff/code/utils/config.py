import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import random
import numpy as np
import torch

# Global configuration dictionary
_CONFIG = {
    "seed": 42,
    "paths": {},
    "hyperparameters": {},
}

def set_global_seed(seed: int) -> None:
    """
    Set the global random seed for reproducibility.
    
    Args:
        seed: Integer seed value
    """
    _CONFIG["seed"] = seed
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

def ensure_directories(paths: List[Union[str, Path]]) -> None:
    """
    Ensure that the specified directories exist.
    
    Args:
        paths: List of directory paths to create
    """
    for path in paths:
        dir_path = Path(path)
        dir_path.mkdir(parents=True, exist_ok=True)

def get_config_summary() -> Dict[str, Any]:
    """
    Get a summary of the current configuration.
    
    Returns:
        Dictionary containing configuration summary
    """
    return {
        "seed": _CONFIG["seed"],
        "paths": {k: str(v) for k, v in _CONFIG["paths"].items()},
        "hyperparameters": _CONFIG["hyperparameters"],
    }

def initialize_paths(project_root: Path = None) -> Dict[str, Path]:
    """
    Initialize standard project paths.
    
    Args:
        project_root: Root directory of the project. Defaults to current working directory.
        
    Returns:
        Dictionary mapping path names to Path objects
    """
    if project_root is None:
        project_root = Path.cwd()
    
    paths = {
        "root": project_root,
        "code": project_root / "code",
        "data": project_root / "data",
        "data_raw": project_root / "data" / "raw",
        "data_processed": project_root / "data" / "processed",
        "data_artifacts": project_root / "data" / "artifacts",
        "tests": project_root / "tests",
        "state": project_root / "state",
        "figures": project_root / "figures",
    }
    
    _CONFIG["paths"] = paths
    ensure_directories(paths.values())
    
    return paths

def get_path(name: str) -> Path:
    """
    Get a configured path by name.
    
    Args:
        name: Name of the path to retrieve
        
    Returns:
        Path object
        
    Raises:
        KeyError: If path name is not found
    """
    if name not in _CONFIG["paths"]:
        raise KeyError(f"Path '{name}' not found in configuration")
    return _CONFIG["paths"][name]

def set_hyperparameter(name: str, value: Any) -> None:
    """
    Set a hyperparameter value.
    
    Args:
        name: Name of the hyperparameter
        value: Value to set
    """
    _CONFIG["hyperparameters"][name] = value

def get_hyperparameter(name: str, default: Any = None) -> Any:
    """
    Get a hyperparameter value.
    
    Args:
        name: Name of the hyperparameter
        default: Default value if not found
        
    Returns:
        Hyperparameter value
    """
    return _CONFIG["hyperparameters"].get(name, default)
