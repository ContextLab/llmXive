"""
Configuration management for the llmXive research pipeline.

Provides centralized path management and random seed pinning for reproducibility.
"""
import os
import random
from pathlib import Path
from typing import Any, Dict, Optional
import numpy as np

# Project root relative to this file
_PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Base directories as defined in plan.md and tasks.md
_DATA_RAW = _PROJECT_ROOT / "data" / "raw"
_DATA_PROCESSED = _PROJECT_ROOT / "data" / "processed"
_DATA_PRIMES = _PROJECT_ROOT / "data" / "primes"
_DATA_TARGETS = _PROJECT_ROOT / "data" / "targets"
_STATE_DIR = _PROJECT_ROOT / "state"

# Default random seed for reproducibility
_DEFAULT_SEED = 42

# Cache for resolved paths
_PATH_CACHE: Dict[str, Path] = {}

def get_path(name: str) -> Path:
    """
    Retrieve a configured directory path by logical name.
    
    Args:
        name: Logical name of the directory (e.g., 'raw', 'processed', 'primes', 'targets', 'state')
    
    Returns:
        Absolute Path object for the requested directory.
    
    Raises:
        ValueError: If the requested name is not configured.
    """
    if name in _PATH_CACHE:
        return _PATH_CACHE[name]
    
    mapping = {
        "raw": _DATA_RAW,
        "processed": _DATA_PROCESSED,
        "primes": _DATA_PRIMES,
        "targets": _DATA_TARGETS,
        "state": _STATE_DIR,
    }
    
    if name not in mapping:
        raise ValueError(f"Unknown path name: {name}. Available: {list(mapping.keys())}")
    
    _PATH_CACHE[name] = mapping[name]
    return mapping[name]

def set_seed(seed: Optional[int] = None) -> int:
    """
    Set random seeds for reproducibility across Python, NumPy, and random modules.
    
    Args:
        seed: Integer seed value. If None, uses the default seed (_DEFAULT_SEED).
    
    Returns:
        The seed value that was set.
    """
    if seed is None:
        seed = _DEFAULT_SEED
    
    random.seed(seed)
    np.random.seed(seed)
    
    # Log the seed for reproducibility tracking
    import logging
    logging.getLogger(__name__).info(f"Random seed set to: {seed}")
    
    return seed

def ensure_directories(paths: Optional[list] = None) -> None:
    """
    Ensure that the specified directories exist, creating them if necessary.
    
    Args:
        paths: List of logical path names to ensure. If None, ensures all configured paths.
    """
    if paths is None:
        paths = ["raw", "processed", "primes", "targets", "state"]
    
    for name in paths:
        try:
            path = get_path(name)
            path.mkdir(parents=True, exist_ok=True)
            import logging
            logging.getLogger(__name__).debug(f"Ensured directory exists: {path}")
        except ValueError as e:
            logging.getLogger(__name__).warning(f"Skipping unknown path '{name}': {e}")
        except OSError as e:
            import logging
            logging.getLogger(__name__).error(f"Failed to create directory {name}: {e}")
            raise

# Convenience function to get all base directories
def get_all_base_paths() -> Dict[str, Path]:
    """
    Get a dictionary of all configured base paths.
    
    Returns:
        Dictionary mapping logical names to Path objects.
    """
    return {
        "raw": get_path("raw"),
        "processed": get_path("processed"),
        "primes": get_path("primes"),
        "targets": get_path("targets"),
        "state": get_path("state"),
    }