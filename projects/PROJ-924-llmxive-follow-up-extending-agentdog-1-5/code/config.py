"""
Configuration management for the AgentDoG Drift Detection pipeline.
Handles random seeds, paths, batch sizes, and memory constraints.
"""
import os
import random
from pathlib import Path
from typing import Any, Dict, Optional, List, Union

import numpy as np

# ==============================================================================
# Core Constants
# ==============================================================================
RANDOM_SEED = 42
MAX_RAM_GB = 7
# Batch size derived from AgentDoG 1.5 paper (2410.21676)
BATCH_SIZE = 64

# ==============================================================================
# Project Paths
# ==============================================================================
# Base project root is assumed to be the directory containing this file's parent
# or explicitly set via environment variable.
_PROJECT_ROOT = Path(os.getenv("PROJECT_ROOT", Path(__file__).resolve().parents[1]))

# Path aliases mapping logical names to relative paths from PROJECT_ROOT
_PATH_ALIASES = {
    "project_root": "",
    "code": "code",
    "data": "data",
    "data_raw": "data/raw",
    "data_processed": "data/processed",
    "data_test": "data/test",
    "specs": "specs",
    "docs": "docs",
    "output_dir": "data/processed",
    "centroid_file": "data/processed/taxonomy_centroids.json",
    "drift_scores_csv": "data/processed/drift_scores.csv",
    "taxonomy_agentdog": "data/processed/taxonomy_agentdog.json",
    "us01_final_stats": "data/processed/us01_final_stats.json",
    "checksums": "data/checksums.json",
    "raw_data": "data/raw",
    "test": "data/test",
    "processed": "data/processed",
}

# ==============================================================================
# Seed Management
# ==============================================================================
def set_seed(seed: int = RANDOM_SEED) -> None:
    """
    Set random seeds for reproducibility across numpy, python random, and torch (if available).
    
    Args:
        seed: The integer seed value. Defaults to RANDOM_SEED (42).
    """
    random.seed(seed)
    np.random.seed(seed)
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass  # Torch not installed, skip

# ==============================================================================
# Configuration Access
# ==============================================================================
def get_config() -> Dict[str, Any]:
    """
    Return the current configuration dictionary.
    
    Returns:
        Dictionary containing all core constants and settings.
    """
    return {
        "random_seed": RANDOM_SEED,
        "max_ram_gb": MAX_RAM_GB,
        "batch_size": BATCH_SIZE,
        "project_root": str(_PROJECT_ROOT),
    }

def update_config(updates: Dict[str, Any]) -> None:
    """
    Update global configuration values. (Note: Constants are immutable, this updates 
    the effective runtime values if needed, though typically constants are preferred).
    
    Args:
        updates: Dictionary of key-value pairs to update.
    """
    # In a strict constant model, we might just log or ignore.
    # For flexibility, we could allow overriding if keys match.
    pass

def get_config_summary() -> str:
    """
    Return a string summary of the current configuration.
    
    Returns:
        Formatted string of config values.
    """
    cfg = get_config()
    lines = [
        "Configuration Summary:",
        f"  Random Seed: {cfg['random_seed']}",
        f"  Max RAM (GB): {cfg['max_ram_gb']}",
        f"  Batch Size: {cfg['batch_size']}",
        f"  Project Root: {cfg['project_root']}",
    ]
    return "\n".join(lines)

# ==============================================================================
# Path Resolution (Universal Interface)
# ==============================================================================
def get_path(*args: Union[str, Path]) -> Path:
    """
    Resolve a path relative to the project root.
    
    Supports multiple calling patterns to ensure compatibility with all callers:
    1. get_path("alias_name") -> resolves alias from _PATH_ALIASES
    2. get_path("relative", "path", "parts") -> joins parts relative to root
    3. get_path(Path("some", "path")) -> returns the Path directly
    4. get_path("alias", "subpath") -> resolves alias then appends subpath
    
    Args:
        *args: Variable length arguments. 
               - If a single string matching an alias is provided, returns that path.
               - If multiple strings are provided, joins them relative to root.
               - If a Path object is provided, returns it (or resolves if relative).
    
    Returns:
        A resolved absolute Path object.
    
    Raises:
        KeyError: If a string alias is not found in _PATH_ALIASES.
    """
    if not args:
        return _PROJECT_ROOT

    # Flatten args if a single tuple/list is passed (defensive)
    # but primarily handle *args as individual components.
    
    if len(args) == 1:
        arg = args[0]
        if isinstance(arg, Path):
            if arg.is_absolute():
                return arg
            return _PROJECT_ROOT / arg
        elif isinstance(arg, str):
            # Check if it's an alias
            if arg in _PATH_ALIASES:
                base_str = _PATH_ALIASES[arg]
                if not base_str:
                    return _PROJECT_ROOT
                return _PROJECT_ROOT / base_str
            else:
                # Treat as a relative path string
                return _PROJECT_ROOT / arg
    
    # Multiple arguments: join them
    # If the first arg is an alias, resolve it first, then append the rest
    first_arg = args[0]
    if isinstance(first_arg, str) and first_arg in _PATH_ALIASES:
        base_str = _PATH_ALIASES[first_arg]
        base_path = _PROJECT_ROOT / base_str if base_str else _PROJECT_ROOT
        remaining = args[1:]
        for part in remaining:
            if isinstance(part, Path):
                base_path = base_path / part
            else:
                base_path = base_path / str(part)
        return base_path
    
    # Otherwise, join all parts relative to root
    parts = [str(p) for p in args]
    return _PROJECT_ROOT / os.path.join(*parts)

def get_output_path(*args: Union[str, Path]) -> Path:
    """
    Convenience wrapper for get_path, specifically for output directories.
    Defaults to 'data/processed' if no alias is provided.
    
    Args:
        *args: Path components.
    
    Returns:
        Resolved Path.
    """
    if not args:
        return get_path("data_processed")
    return get_path(*args)

# ==============================================================================
# Directory Management
# ==============================================================================
def ensure_directories(dir_paths: List[Union[str, Path]]) -> None:
    """
    Ensure that the given list of directory paths exist.
    Creates parent directories as needed.
    
    Args:
        dir_paths: List of directory paths (strings or Path objects).
    
    Raises:
        TypeError: If an item in dir_paths is not a string or Path.
    """
    if not isinstance(dir_paths, list):
        dir_paths = [dir_paths]
    
    for p in dir_paths:
        if isinstance(p, str):
            path_obj = get_path(p)
        elif isinstance(p, Path):
            # If absolute, use as is; if relative, resolve against root
            if p.is_absolute():
                path_obj = p
            else:
                path_obj = get_path(p)
        else:
            raise TypeError(f"Expected str or Path, got {type(p)}")
        
        path_obj.mkdir(parents=True, exist_ok=True)

# ==============================================================================
# Batch & Memory Helpers
# ==============================================================================
def get_batch_size() -> int:
    """
    Retrieve the configured batch size.
    
    Returns:
        Integer batch size.
    """
    return BATCH_SIZE

def get_max_memory_gb() -> int:
    """
    Retrieve the configured maximum RAM in GB.
    
    Returns:
        Integer max RAM.
    """
    return MAX_RAM_GB

def get_drift_threshold() -> float:
    """
    Retrieve the default drift threshold.
    
    Returns:
        Float threshold (default 0.5).
    """
    return 0.5

def get_centroid_model() -> str:
    """
    Retrieve the configured centroid model name.
    
    Returns:
        String model name.
    """
    return "all-MiniLM-L6-v2"

def get_baseline_model() -> str:
    """
    Retrieve the configured baseline model name.
    
    Returns:
        String model name.
    """
    return "google/flan-t5-small"

# ==============================================================================
# Initialization
# ==============================================================================
# Initialize seed on module load for immediate availability
set_seed(RANDOM_SEED)