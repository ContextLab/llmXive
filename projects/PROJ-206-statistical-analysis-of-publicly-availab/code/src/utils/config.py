"""
Configuration management module for the llmXive statistical analysis pipeline.

Provides utilities for:
- Path resolution relative to the project root
- Global random seed pinning for reproducibility
- Directory creation and validation
"""
import os
import random
import hashlib
from pathlib import Path
from typing import Any, Dict, Optional, Union

# Global seed state
_SEED: Optional[int] = None
_PROJECT_ROOT: Optional[Path] = None

def get_project_root() -> Path:
    """
    Returns the root directory of the project.
    Assumes the project root is the directory containing the 'code' folder.
    """
    global _PROJECT_ROOT
    if _PROJECT_ROOT is not None:
        return _PROJECT_ROOT

    # Try to detect from __file__ (code/src/utils/config.py -> code -> root)
    current_file = Path(__file__).resolve()
    # Navigate up: config.py -> utils -> src -> code -> root
    # We assume the structure is: <root>/code/src/utils/config.py
    # So root is 4 levels up from this file
    potential_root = current_file.parent.parent.parent.parent
    
    # Fallback: check if 'data' and 'state' exist at this level
    if (potential_root / 'data').exists() and (potential_root / 'state').exists():
        _PROJECT_ROOT = potential_root
        return _PROJECT_ROOT

    # If detection fails, assume current working directory
    # This is a fallback for interactive usage
    _PROJECT_ROOT = Path.cwd()
    return _PROJECT_ROOT

def get_data_root() -> Path:
    """Returns the path to the data directory."""
    return get_project_root() / 'data'

def get_state_root() -> Path:
    """Returns the path to the state directory."""
    return get_project_root() / 'state'

def get_code_root() -> Path:
    """Returns the path to the code directory."""
    return get_project_root() / 'code'

def get_figures_root() -> Path:
    """Returns the path to the figures directory (created if needed)."""
    figures_path = get_project_root() / 'figures'
    ensure_dir(figures_path)
    return figures_path

def get_spec_root() -> Path:
    """Returns the path to the specs directory."""
    return get_project_root() / 'specs'

def resolve_path(path: Union[str, Path], base: Optional[Path] = None) -> Path:
    """
    Resolves a relative or absolute path.
    
    Args:
        path: The path to resolve.
        base: The base directory. Defaults to project root if None.
    
    Returns:
        A resolved Path object.
    """
    if isinstance(path, str):
        path = Path(path)
    
    if path.is_absolute():
        return path.resolve()
    
    if base is None:
        base = get_project_root()
    
    return (base / path).resolve()

def set_seed(seed: int) -> None:
    """
    Sets the global random seed for reproducibility.
    
    This function seeds:
    - Python's random module
    - NumPy's random module (if available)
    
    Args:
        seed: The integer seed value.
    """
    global _SEED
    _SEED = seed
    random.seed(seed)
    
    try:
        import numpy as np
        np.random.seed(seed)
    except ImportError:
        pass

def get_seed() -> Optional[int]:
    """Returns the currently set global seed, or None if not set."""
    return _SEED

def compute_file_hash(file_path: Union[str, Path]) -> str:
    """
    Computes the SHA-256 hash of a file's contents.
    
    Args:
        file_path: Path to the file to hash.
    
    Returns:
        Hexadecimal string representation of the SHA-256 hash.
    
    Raises:
        FileNotFoundError: If the file does not exist.
    """
    file_path = resolve_path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def ensure_dir(dir_path: Union[str, Path]) -> Path:
    """
    Ensures a directory exists, creating it if necessary.
    
    Args:
        dir_path: The directory path to ensure.
    
    Returns:
        The resolved Path object for the directory.
    """
    path = resolve_path(dir_path)
    path.mkdir(parents=True, exist_ok=True)
    return path

def get_config() -> Dict[str, Any]:
    """
    Returns a dictionary of key configuration paths and settings.
    
    Returns:
        Dictionary containing root paths and seed status.
    """
    return {
        "project_root": str(get_project_root()),
        "data_root": str(get_data_root()),
        "state_root": str(get_state_root()),
        "code_root": str(get_code_root()),
        "figures_root": str(get_figures_root()),
        "spec_root": str(get_spec_root()),
        "seed_set": _SEED is not None,
        "seed_value": _SEED
    }

# Convenience function to initialize standard directories
def initialize_project_structure() -> None:
    """
    Ensures all standard project directories exist.
    """
    ensure_dir(get_data_root() / 'raw')
    ensure_dir(get_data_root() / 'processed')
    ensure_dir(get_state_root() / 'projects')
    ensure_dir(get_figures_root())
    # Ensure src/utils exists if running from root
    ensure_dir(get_code_root() / 'src' / 'utils')
    ensure_dir(get_code_root() / 'src' / 'data')
    ensure_dir(get_code_root() / 'src' / 'models')
    ensure_dir(get_code_root() / 'src' / 'evaluation')

if __name__ == "__main__":
    # Simple self-test to verify path resolution
    print("Project Root:", get_project_root())
    print("Data Root:", get_data_root())
    print("State Root:", get_state_root())
    print("Config:", get_config())
    
    # Test seed setting
    set_seed(42)
    print("Seed set to:", get_seed())
    
    # Test directory creation
    test_dir = get_data_root() / 'test_temp'
    ensure_dir(test_dir)
    print("Test directory created/verified:", test_dir.exists())
    
    # Cleanup
    import shutil
    if test_dir.exists():
        shutil.rmtree(test_dir)
        print("Test directory cleaned up.")
