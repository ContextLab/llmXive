"""
Configuration management for llmXive project.
Handles global seed pinning, path management, and environment configuration.
"""
import os
import random
from pathlib import Path
from typing import Optional

import numpy as np
import torch

# Global project root
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Configuration constants
GLOBAL_SEED = 42
DEFAULT_TIMEOUT = 3600  # 1 hour default timeout
MAX_CPU_MEMORY_GB = 14  # Default memory limit for CPU runs

def set_global_seed(seed: Optional[int] = None) -> None:
    """
    Set global random seeds for reproducibility.
    
    Args:
        seed: Random seed value. Defaults to GLOBAL_SEED if None.
    """
    if seed is None:
        seed = GLOBAL_SEED
    
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    
    # For deterministic behavior (may impact performance)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False

def get_project_root() -> Path:
    """Return the absolute path to the project root."""
    return _PROJECT_ROOT

def get_data_dir(subdir: Optional[str] = None) -> Path:
    """
    Get path to data directory.
    
    Args:
        subdir: Optional subdirectory (e.g., 'raw', 'interim', 'processed')
    
    Returns:
        Path object pointing to the requested data directory.
    """
    data_root = _PROJECT_ROOT / "data"
    if subdir:
        return data_root / subdir
    return data_root

def get_code_dir(subdir: Optional[str] = None) -> Path:
    """
    Get path to code directory.
    
    Args:
        subdir: Optional subdirectory (e.g., 'utils', 'inference', 'scripts')
    
    Returns:
        Path object pointing to the requested code directory.
    """
    code_root = _PROJECT_ROOT / "code"
    if subdir:
        return code_root / subdir
    return code_root

def get_tests_dir(subdir: Optional[str] = None) -> Path:
    """
    Get path to tests directory.
    
    Args:
        subdir: Optional subdirectory (e.g., 'unit', 'integration')
    
    Returns:
        Path object pointing to the requested tests directory.
    """
    tests_root = _PROJECT_ROOT / "tests"
    if subdir:
        return tests_root / subdir
    return tests_root

def get_state_dir(project_id: str, subdir: Optional[str] = None) -> Path:
    """
    Get path to state directory for a specific project.
    
    Args:
        project_id: Project identifier (e.g., 'PROJ-922')
        subdir: Optional subdirectory within the project state folder.
    
    Returns:
        Path object pointing to the requested state directory.
    """
    state_root = _PROJECT_ROOT / "state" / "projects" / project_id
    if subdir:
        return state_root / subdir
    return state_root

def get_figures_dir() -> Path:
    """Get path to figures directory for output plots."""
    return get_data_dir() / "figures"

def ensure_dir(path: Path) -> None:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        path: Path object to ensure exists.
    """
    path.mkdir(parents=True, exist_ok=True)

def get_config_from_env(key: str, default: Optional[str] = None) -> str:
    """
    Retrieve a configuration value from environment variables.
    
    Args:
        key: Environment variable name.
        default: Default value if key is not found.
    
    Returns:
        The environment variable value or default.
    
    Raises:
        KeyError: If key is not found and no default is provided.
    """
    value = os.getenv(key)
    if value is None:
        if default is None:
            raise KeyError(f"Environment variable '{key}' is not set")
        return default
    return value

def get_device() -> str:
    """
    Determine the device to use (cpu or cuda).
    
    Returns:
        String 'cuda' if available, otherwise 'cpu'.
    """
    if torch.cuda.is_available():
        return "cuda"
    return "cpu"

def get_model_cache_dir() -> Path:
    """Get the directory for caching downloaded models."""
    cache_dir = get_data_dir() / "models_cache"
    ensure_dir(cache_dir)
    return cache_dir

def get_output_path(filename: str, subdir: Optional[str] = None) -> Path:
    """
    Construct a full output path in the data directory.
    
    Args:
        filename: Name of the output file.
        subdir: Optional subdirectory (e.g., 'interim', 'processed').
    
    Returns:
        Full Path object for the output file.
    """
    base_dir = get_data_dir(subdir) if subdir else get_data_dir()
    ensure_dir(base_dir)
    return base_dir / filename

# Initialize seeds on module import for immediate reproducibility
set_global_seed(GLOBAL_SEED)