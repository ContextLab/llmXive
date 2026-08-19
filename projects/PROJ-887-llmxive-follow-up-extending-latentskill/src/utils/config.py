"""
Configuration management for llmXive project.
Handles seed pinning, path resolution, and environment variable loading.
"""
import os
import sys
import random
import numpy as np
from pathlib import Path
from typing import Optional, Dict, Any, List, Union
import yaml

# Project root is the parent of the 'src' directory
_PROJECT_ROOT: Optional[Path] = None

# Default seed for reproducibility
DEFAULT_SEED = 42

# OOD Threshold for retrieval (defined in T004b)
OOD_THRESHOLD = 0.5

def get_project_root() -> Path:
    """
    Returns the absolute path to the project root.
    Caches the result on first call.
    """
    global _PROJECT_ROOT
    if _PROJECT_ROOT is None:
        # Assume src/ is at repo root or parent of this file
        current_file = Path(__file__).resolve()
        # Traverse up to find the directory containing 'src'
        # Standard structure: repo_root/src/utils/config.py
        _PROJECT_ROOT = current_file.parent.parent.parent
        # Fallback if running from scripts/ or similar
        if not (_PROJECT_ROOT / "src").exists():
            _PROJECT_ROOT = current_file.parent.parent.parent.parent
    return _PROJECT_ROOT

def get_data_path(subpath: Optional[str] = None, project_root: Optional[Path] = None) -> Path:
    """
    Resolves data directory paths.
    
    Args:
        subpath: Optional subdirectory name (e.g., 'raw', 'processed', 'results').
                 If None, returns the data root.
        project_root: Optional override for project root. Defaults to get_project_root().
    
    Returns:
        Path object to the requested data directory.
    """
    root = project_root if project_root is not None else get_project_root()
    data_root = root / "data"
    
    if subpath is None:
        return data_root
    
    return data_root / subpath

def get_artifacts_path(subpath: Optional[str] = None, project_root: Optional[Path] = None) -> Path:
    """
    Resolves artifacts directory paths.
    
    Args:
        subpath: Optional subdirectory name.
        project_root: Optional override for project root.
        
    Returns:
        Path object to the requested artifacts directory.
    """
    root = project_root if project_root is not None else get_project_root()
    artifacts_root = root / "artifacts"
    
    if subpath is None:
        return artifacts_root
    
    return artifacts_root / subpath

def get_results_path(subpath: Optional[str] = None, project_root: Optional[Path] = None) -> Path:
    """
    Resolves results directory paths.
    
    Args:
        subpath: Optional subdirectory name.
        project_root: Optional override for project root.
        
    Returns:
        Path object to the requested results directory.
    """
    root = project_root if project_root is not None else get_project_root()
    results_root = root / "data" / "results"
    
    if subpath is None:
        return results_root
    
    return results_root / subpath

def ensure_directories(paths: Optional[List[Union[Path, str]]] = None, 
                       *args, 
                       project_root: Optional[Path] = None) -> None:
    """
    Ensures that the specified directories exist.
    
    This function is designed to be tolerant of various call signatures:
    1. ensure_directories([Path(...), ...])
    2. ensure_directories() -> Does nothing (no-op)
    3. ensure_directories(project_root=Path(...)) -> No-op if no paths provided
    4. ensure_directories(*args) -> Ignores positional args if not a list of paths
    
    Args:
        paths: Optional list of Path objects or strings to ensure.
        project_root: Optional project root (unused if paths is None).
    """
    # Handle the case where no arguments are passed or only keyword args are passed
    if paths is None:
        return

    # If paths is a single Path or string, wrap it in a list
    if isinstance(paths, (Path, str)):
        paths = [paths]
    
    # Iterate and create directories
    for p in paths:
        target = Path(p)
        target.mkdir(parents=True, exist_ok=True)

def set_seed(seed: int = DEFAULT_SEED) -> None:
    """
    Sets the random seed for reproducibility across Python, NumPy, and PyTorch (if available).
    
    Args:
        seed: Integer seed value.
    """
    random.seed(seed)
    np.random.seed(seed)
    
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass  # PyTorch not installed

def load_config(config_path: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
    """
    Loads a YAML configuration file.
    
    Args:
        config_path: Path to the config file. Defaults to 'config.yaml' in project root.
        
    Returns:
        Dictionary containing configuration values.
    """
    if config_path is None:
        root = get_project_root()
        config_path = root / "config.yaml"
    else:
        config_path = Path(config_path)
        
    if not config_path.exists():
        # Return empty config if file doesn't exist, rather than failing
        return {}
        
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f) or {}

# T004b: Export OOD_THRESHOLD directly as requested by the task description
# It is also accessible via the module level.
__all__ = [
    'get_project_root',
    'get_data_path',
    'get_artifacts_path',
    'get_results_path',
    'ensure_directories',
    'set_seed',
    'load_config',
    'OOD_THRESHOLD',
    'DEFAULT_SEED'
]