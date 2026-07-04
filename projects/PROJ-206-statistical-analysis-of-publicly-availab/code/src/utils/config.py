"""
Configuration management module for the statistical poll aggregation pipeline.

Responsibilities:
- Seed pinning for reproducibility
- Path resolution for project directories (data, state, src)
- Environment variable overrides
"""

import os
import random
from pathlib import Path
from typing import Optional, Dict, Any

# Default seed for reproducibility
DEFAULT_SEED = 42

# Project root detection
def get_project_root() -> Path:
    """
    Detect the project root directory.
    Assumes the code is running from within the project tree.
    Looks for the 'data' directory or 'requirements.txt' to anchor the root.
    """
    current = Path.cwd()
    # Check if running from code/ or src/ or root
    candidates = [current, current.parent, current.parent.parent]
    
    for candidate in candidates:
        if (candidate / "requirements.txt").exists() or (candidate / "data").exists():
            return candidate
    
    # Fallback to current directory if no marker found
    return current

def resolve_paths(project_root: Optional[Path] = None) -> Dict[str, Path]:
    """
    Resolve absolute paths for all critical project directories.
    
    Returns a dictionary with keys:
    - 'root': Project root
    - 'data_raw': data/raw
    - 'data_processed': data/processed
    - 'state': state/projects
    - 'src': src (source code)
    - 'specs': specs
    """
    root = project_root or get_project_root()
    
    paths = {
        'root': root,
        'data_raw': root / 'data' / 'raw',
        'data_processed': root / 'data' / 'processed',
        'state': root / 'state' / 'projects',
        'src': root / 'src',
        'specs': root / 'specs',
        'code': root / 'code', # For scripts in code/
        'tests': root / 'tests',
    }
    
    # Ensure directories exist (creation handled by setup tasks, but safe to ensure)
    for key, path in paths.items():
        if key in ['data_raw', 'data_processed', 'state']:
            path.mkdir(parents=True, exist_ok=True)
    
    return paths

def set_seed(seed: Optional[int] = None) -> int:
    """
    Set the random seed for reproducibility across numpy, random, and torch (if available).
    
    Args:
        seed: Optional seed integer. If None, uses DEFAULT_SEED.
    
    Returns:
        The seed value that was set.
    """
    effective_seed = seed if seed is not None else DEFAULT_SEED
    
    # Set for Python standard library
    random.seed(effective_seed)
    
    # Set for NumPy if available
    try:
        import numpy as np
        np.random.seed(effective_seed)
    except ImportError:
        pass
    
    # Set for PyTorch if available
    try:
        import torch
        torch.manual_seed(effective_seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(effective_seed)
    except ImportError:
        pass
    
    # Set for PyMC if available
    try:
        import pymc as pm
        # PyMC often uses numpy random state, but explicit setting is good practice
        pm.set_seed(effective_seed)
    except ImportError:
        pass
    
    return effective_seed

def get_config_value(key: str, default: Any = None) -> Any:
    """
    Retrieve a configuration value from environment variables.
    
    Priority:
    1. Environment variable
    2. Default value
    
    Args:
        key: The environment variable name (e.g., 'POLL_DATA_SOURCE')
        default: The default value if the env var is not set
    
    Returns:
        The value from the environment or the default.
    """
    return os.getenv(key, default)

def validate_environment(paths: Dict[str, Path]) -> bool:
    """
    Validate that the resolved paths are writable and exist.
    
    Returns:
        True if validation passes, False otherwise.
    """
    required_dirs = ['data_raw', 'data_processed', 'state', 'src']
    for key in required_dirs:
        if key not in paths:
            continue
        path = paths[key]
        if not path.exists():
            # Attempt to create if missing (setup task should have done this, but defensive)
            try:
                path.mkdir(parents=True, exist_ok=True)
            except OSError:
                return False
        if not os.access(path, os.W_OK):
            return False
    return True

# Singleton-like configuration holder (optional, for easy access)
_config_cache: Optional[Dict[str, Path]] = None
_seed_set: bool = False

def get_config() -> Dict[str, Path]:
    """
    Get the global configuration paths. Initializes if not already set.
    """
    global _config_cache
    if _config_cache is None:
        _config_cache = resolve_paths()
        validate_environment(_config_cache)
    return _config_cache

def reset_config() -> None:
    """
    Reset the configuration cache. Useful for testing.
    """
    global _config_cache
    _config_cache = None

# Convenience functions for common paths
def get_data_processed_path() -> Path:
    """Get the path to the processed data directory."""
    return get_config()['data_processed']

def get_state_path() -> Path:
    """Get the path to the state directory."""
    return get_config()['state']

def get_raw_data_path() -> Path:
    """Get the path to the raw data directory."""
    return get_config()['data_raw']

def get_src_path() -> Path:
    """Get the path to the source code directory."""
    return get_config()['src']