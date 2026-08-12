"""
Configuration management for the llmXive research pipeline.
Handles random seed management, global constants, and path resolution.
"""
import os
import random
from pathlib import Path
from typing import Any, Dict, Optional

# --- Global Constants ---
# Number of null distribution permutations per series for robust statistical testing.
# Addresses reviewer concern regarding ambiguity of "sufficient number".
NUM_NULL_PER_SERIES: int = 1000

# Default random seed for reproducibility
DEFAULT_SEED: int = 42

# Project root directory (relative to script execution)
_PROJECT_ROOT: Optional[Path] = None

def get_project_root() -> Path:
    """
    Returns the project root directory.
    If not explicitly set, defaults to the parent of the 'src' directory.
    """
    global _PROJECT_ROOT
    if _PROJECT_ROOT is not None:
        return _PROJECT_ROOT

    # Default heuristic: assume code/ is the root or parent of src
    current_file = Path(__file__)
    # Try to find 'src' in the path
    src_index = None
    parts = current_file.parts
    for i, part in enumerate(parts):
        if part == 'src':
            src_index = i
            break

    if src_index is not None:
        # Project root is the directory containing 'src'
        _PROJECT_ROOT = Path(*parts[:src_index])
    else:
        # Fallback: assume current working directory
        _PROJECT_ROOT = Path.cwd()

    return _PROJECT_ROOT

def set_project_root(root: Path) -> None:
    """Explicitly set the project root directory."""
    global _PROJECT_ROOT
    _PROJECT_ROOT = Path(root)

def get_path(*relative_path_parts: str) -> Path:
    """
    Construct an absolute path relative to the project root.

    Args:
        *relative_path_parts: Components of the relative path.

    Returns:
        Absolute Path object.
    """
    root = get_project_root()
    return root.joinpath(*relative_path_parts)

def ensure_dirs(*path_parts: str) -> Path:
    """
    Ensure a directory exists, creating it if necessary.

    Args:
        *path_parts: Components of the directory path.

    Returns:
        The created/existing directory Path.
    """
    target_dir = get_path(*path_parts)
    target_dir.mkdir(parents=True, exist_ok=True)
    return target_dir

def set_seed(seed: Optional[int] = None) -> None:
    """
    Set the random seed for reproducibility across numpy, random, and torch (if available).

    Args:
        seed: The seed value. Defaults to DEFAULT_SEED if None.
    """
    if seed is None:
        seed = DEFAULT_SEED

    random.seed(seed)
    try:
        import numpy as np
        np.random.seed(seed)
    except ImportError:
        pass

    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass

    # Store seed in environment for external tools if needed
    os.environ['PYTHONHASHSEED'] = str(seed)