"""
Configuration management for the statistical analysis pipeline.

Handles:
- Seed pinning for reproducibility
- Path resolution relative to project root
- Environment variable overrides
"""
import os
import random
import hashlib
from pathlib import Path
from typing import Any, Dict, Optional, Union

# Project root is assumed to be the parent of 'code' directory
# Adjust if project structure differs
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_DATA_ROOT = _PROJECT_ROOT / "data"
_STATE_ROOT = _PROJECT_ROOT / "state"
_CODE_ROOT = _PROJECT_ROOT / "code"
_FIGURES_ROOT = _PROJECT_ROOT / "figures"
_SPEC_ROOT = _PROJECT_ROOT / "specs"

# Default seed for reproducibility
DEFAULT_SEED = 42


def get_project_root() -> Path:
    """Return the absolute path to the project root directory."""
    return _PROJECT_ROOT


def get_data_root() -> Path:
    """Return the absolute path to the data directory."""
    return _DATA_ROOT


def get_state_root() -> Path:
    """Return the absolute path to the state directory."""
    return _STATE_ROOT


def get_code_root() -> Path:
    """Return the absolute path to the code directory."""
    return _CODE_ROOT


def get_figures_root() -> Path:
    """Return the absolute path to the figures directory."""
    return _FIGURES_ROOT


def get_spec_root() -> Path:
    """Return the absolute path to the specs directory."""
    return _SPEC_ROOT


def resolve_path(base: str, relative: str) -> Path:
    """
    Resolve a relative path against a base directory.
    
    Args:
        base: Base directory name (e.g., 'data', 'state', 'code')
        relative: Relative path within that base directory
        
    Returns:
        Absolute Path object
        
    Raises:
        ValueError: If base directory is not recognized
    """
    base_paths = {
        'data': get_data_root(),
        'state': get_state_root(),
        'code': get_code_root(),
        'figures': get_figures_root(),
        'specs': get_spec_root(),
    }
    
    if base not in base_paths:
        raise ValueError(f"Unknown base directory: {base}. Must be one of {list(base_paths.keys())}")
        
    return base_paths[base] / relative


def set_seed(seed: Optional[int] = None) -> int:
    """
    Set random seeds for reproducibility.
    
    Args:
        seed: Random seed value. If None, uses DEFAULT_SEED.
            
    Returns:
        The seed value that was set
    """
    if seed is None:
        seed = DEFAULT_SEED
        
    # Set seeds for standard libraries
    random.seed(seed)
    
    # Try to set numpy seed if available
    try:
        import numpy as np
        np.random.seed(seed)
    except ImportError:
        pass
        
    # Try to set torch seed if available
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass
        
    return seed


def get_seed() -> int:
    """
    Get the current seed value from environment or default.
    
    Returns:
        Seed value as integer
    """
    env_seed = os.environ.get("LLMXIVE_SEED")
    if env_seed is not None:
        try:
            return int(env_seed)
        except ValueError:
            pass
    return DEFAULT_SEED


def compute_file_hash(file_path: Union[str, Path]) -> str:
    """
    Compute SHA-256 hash of a file for integrity verification.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Hexadecimal hash string
        
    Raises:
        FileNotFoundError: If file does not exist
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
        
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def ensure_dir(dir_path: Union[str, Path]) -> Path:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        dir_path: Path to the directory
        
    Returns:
        The absolute Path object
    """
    path = Path(dir_path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_config() -> Dict[str, Any]:
    """
    Get the full configuration dictionary.
    
    Returns:
        Dictionary containing all configuration values
    """
    return {
        "project_root": str(get_project_root()),
        "data_root": str(get_data_root()),
        "state_root": str(get_state_root()),
        "code_root": str(get_code_root()),
        "figures_root": str(get_figures_root()),
        "spec_root": str(get_spec_root()),
        "seed": get_seed(),
        "default_seed": DEFAULT_SEED,
    }