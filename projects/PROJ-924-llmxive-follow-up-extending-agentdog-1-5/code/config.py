"""
Configuration management for the llmXive Drift Detection pipeline.

This module centralizes project-wide settings including random seeds,
memory limits, batch sizes, and path resolution.
"""
import os
import random
from pathlib import Path
from typing import Any, Dict, Optional, List

import numpy as np

# --- Core Constants ---
RANDOM_SEED = 42
MAX_RAM_GB = 7
BATCH_SIZE = 64

# --- Project Root Resolution ---
# Determine the project root based on the current working directory structure.
# We assume the code runs from the project root or a subdirectory.
def _get_project_root() -> Path:
    """
    Locate the project root directory.
    
    Strategy:
    1. If running from 'projects/PROJ-.../code', go up two levels.
    2. If running from 'projects/PROJ-...', go up one level.
    3. Default to current working directory if not found.
    """
    cwd = Path.cwd()
    
    # Check if we are deep in the project structure
    if cwd.name == 'code' and cwd.parent.name.startswith('PROJ-924'):
        return cwd.parent.parent
    
    if cwd.name.startswith('PROJ-924'):
        return cwd
        
    return cwd

PROJECT_ROOT = _get_project_root()

# --- Global State ---
_config: Dict[str, Any] = {
    "random_seed": RANDOM_SEED,
    "max_ram_gb": MAX_RAM_GB,
    "batch_size": BATCH_SIZE,
    "project_root": PROJECT_ROOT,
}

# --- Helper Functions ---

def set_seed(seed: Optional[int] = None) -> None:
    """
    Set the random seed for reproducibility across numpy, random, and torch (if available).
    
    Args:
        seed: The seed value. Defaults to RANDOM_SEED if None.
    """
    if seed is None:
        seed = RANDOM_SEED
    
    random.seed(seed)
    np.random.seed(seed)
    
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass  # PyTorch not installed, skip

def get_config() -> Dict[str, Any]:
    """
    Return the current configuration dictionary.
    
    Returns:
        A copy of the configuration dictionary.
    """
    return _config.copy()

def update_config(key: str, value: Any) -> None:
    """
    Update a specific configuration value.
    
    Args:
        key: The configuration key to update.
        value: The new value.
    """
    _config[key] = value

def get_config_summary() -> str:
    """
    Generate a human-readable summary of the current configuration.
    
    Returns:
        A formatted string of key configuration values.
    """
    lines = [
        f"Configuration Summary:",
        f"  Random Seed: {_config['random_seed']}",
        f"  Max RAM (GB): {_config['max_ram_gb']}",
        f"  Batch Size: {_config['batch_size']}",
        f"  Project Root: {_config['project_root']}",
    ]
    return "\n".join(lines)

def get_path(relative_path: str) -> Path:
    """
    Resolve a relative path against the project root.
    
    Args:
        relative_path: Path relative to the project root.
        
    Returns:
        An absolute Path object.
    """
    return _config['project_root'] / relative_path

def get_output_path(relative_path: str) -> Path:
    """
    Resolve an output path relative to the project root.
    
    Args:
        relative_path: Path relative to the project root.
        
    Returns:
        An absolute Path object.
    """
    return get_path(relative_path)

def ensure_directories(paths: List[str]) -> None:
    """
    Ensure that the specified directories exist.
    
    Args:
        paths: List of relative paths to ensure exist.
    """
    for path_str in paths:
        full_path = get_path(path_str)
        full_path.mkdir(parents=True, exist_ok=True)

def get_batch_size() -> int:
    """
    Get the configured batch size.
    
    Returns:
        The batch size integer.
    """
    return _config['batch_size']

def get_max_memory_gb() -> int:
    """
    Get the configured maximum RAM limit in GB.
    
    Returns:
        The max RAM integer.
    """
    return _config['max_ram_gb']

def get_drift_threshold() -> float:
    """
    Get the default drift threshold.
    Currently defaults to 0.5, but can be configured.
    
    Returns:
        The threshold float.
    """
    return 0.5

def get_centroid_model() -> str:
    """
    Get the default centroid model name.
    
    Returns:
        The model name string.
    """
    return "sentence-transformers/all-MiniLM-L6-v2"

def get_baseline_model() -> str:
    """
    Get the default baseline model name (Flan-T5).
    
    Returns:
        The model name string.
    """
    return "google/flan-t5-small"

# Initialize seed on module load
set_seed()
