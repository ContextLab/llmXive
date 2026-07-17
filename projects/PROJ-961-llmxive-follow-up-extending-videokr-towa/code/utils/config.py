"""
Configuration management for the llmXive VideoKR project.
Handles seed management, path configuration, and project root detection.
"""
import os
import random
from pathlib import Path
from typing import Any, Dict, Optional, Union

# Project Root Detection
# Assumes the project root is the directory containing the 'code' folder
_PROJECT_ROOT: Optional[Path] = None

def get_project_root() -> Path:
    """
    Returns the project root directory.
    Searches upwards from the current file location.
    """
    global _PROJECT_ROOT
    if _PROJECT_ROOT is not None:
        return _PROJECT_ROOT

    current = Path(__file__).resolve()
    # Traverse up until we find 'code' directory
    for parent in current.parents:
        if (parent / "code").exists() and (parent / "data").exists():
            _PROJECT_ROOT = parent
            return _PROJECT_ROOT
    
    # Fallback: assume current working directory if structure not found
    return Path.cwd()

def get_path(relative_path: Union[str, Path]) -> Path:
    """
    Constructs an absolute path relative to the project root.
    """
    return get_project_root() / relative_path

def ensure_dir(path: Union[str, Path]) -> Path:
    """
    Ensures the directory exists, creating it if necessary.
    Returns the Path object.
    """
    p = get_path(path) if isinstance(path, str) else path
    p.mkdir(parents=True, exist_ok=True)
    return p

def set_seed(seed: int) -> None:
    """
    Sets the random seed for reproducibility across numpy, random, etc.
    """
    random.seed(seed)
    # Note: numpy seed set is usually handled in the specific module 
    # where numpy is imported to avoid circular imports in config.

def get_config() -> Dict[str, Any]:
    """
    Returns a dictionary of standard configuration paths and settings.
    """
    root = get_project_root()
    return {
        "root": root,
        "code_dir": root / "code",
        "data_dir": root / "data",
        "raw_data_dir": root / "data" / "raw",
        "processed_data_dir": root / "data" / "processed",
        "tests_dir": root / "tests",
        "state_dir": root / "state",
        "figures_dir": root / "figures",
        "docs_dir": root / "docs"
    }
