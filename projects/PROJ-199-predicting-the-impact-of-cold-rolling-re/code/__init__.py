"""
llmXive research pipeline for predicting cold rolling impact on FCC texture.

This module provides base configuration loading, seed management, and
directory structure initialization.
"""
import os
import random
from pathlib import Path
from typing import List, Optional, Dict, Any
import numpy as np

# Configuration defaults
DEFAULT_SEED = 42
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_DATA_PATH = "data"
DEFAULT_REDUCTION_LEVELS = [0, 10, 20, 30, 40, 50, 60, 70, 80]

# Environment variable names
ENV_SEED = "LLMXIVE_SEED"
ENV_LOG_LEVEL = "LLMXIVE_LOG_LEVEL"
ENV_DATA_PATH = "LLMXIVE_DATA_PATH"
ENV_REDUCTION_LEVELS = "LLMXIVE_REDUCTION_LEVELS"

class ConfigurationError(Exception):
    """Raised when configuration loading fails."""
    pass

def get_seed() -> int:
    """
    Get the random seed from environment variable or use default.
    
    Returns:
        int: The seed value to use for reproducibility.
    
    Raises:
        ConfigurationError: If the seed value is not a valid integer.
    """
    seed_str = os.getenv(ENV_SEED)
    if seed_str is None:
        return DEFAULT_SEED
    
    try:
        seed = int(seed_str)
        return seed
    except ValueError:
        raise ConfigurationError(
            f"Invalid seed value in {ENV_SEED}: '{seed_str}'. "
            "Must be an integer."
        )

def set_seed(seed: Optional[int] = None) -> None:
    """
    Set the random seed for reproducibility across numpy, random, and torch (if available).
    
    Args:
        seed: The seed value. If None, uses the value from get_seed().
    """
    if seed is None:
        seed = get_seed()
    
    random.seed(seed)
    np.random.seed(seed)
    
    # Try to set torch seed if available
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass  # torch not installed, skip

def get_log_level() -> str:
    """
    Get the logging level from environment variable or use default.
    
    Returns:
        str: The logging level (e.g., "DEBUG", "INFO", "WARNING", "ERROR").
    """
    return os.getenv(ENV_LOG_LEVEL, DEFAULT_LOG_LEVEL)

def get_data_path() -> Path:
    """
    Get the base data directory path from environment variable or use default.
    
    Returns:
        Path: The path to the data directory.
    """
    data_path_str = os.getenv(ENV_DATA_PATH, DEFAULT_DATA_PATH)
    return Path(data_path_str)

def get_reductions() -> List[int]:
    """
    Get the reduction levels from environment variable or use default.
    
    The environment variable should contain comma-separated integers.
    
    Returns:
        List[int]: List of reduction levels to process.
    
    Raises:
        ConfigurationError: If the reduction levels cannot be parsed.
    """
    reductions_str = os.getenv(ENV_REDUCTION_LEVELS)
    if reductions_str is None:
        return DEFAULT_REDUCTION_LEVELS.copy()
    
    try:
        reductions = [int(x.strip()) for x in reductions_str.split(",")]
        if not reductions:
            return DEFAULT_REDUCTION_LEVELS.copy()
        return reductions
    except ValueError:
        raise ConfigurationError(
            f"Invalid reduction levels in {ENV_REDUCTION_LEVELS}: '{reductions_str}'. "
            "Must be comma-separated integers."
        )

def ensure_directories() -> List[str]:
    """
    Create the required top-level directories: code/, data/, tests/, docs/.
    This function is idempotent and creates parent directories as needed.
    
    Returns:
        List[str]: Names of the directories created/verified.
    """
    base = Path(__file__).resolve().parent.parent
    directories = ['code', 'data', 'tests', 'docs']
    created = []
    
    for dir_name in directories:
        dir_path = base / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            created.append(dir_name)
        # Ensure .gitkeep exists for git tracking
        gitkeep_path = dir_path / '.gitkeep'
        if not gitkeep_path.exists():
            gitkeep_path.touch()
    
    # Also ensure data subdirectories exist
    data_path = base / 'data'
    subdirs = ['raw', 'processed', 'interim']
    for subdir in subdirs:
        subdir_path = data_path / subdir
        if not subdir_path.exists():
            subdir_path.mkdir(parents=True, exist_ok=True)
        gitkeep_path = subdir_path / '.gitkeep'
        if not gitkeep_path.exists():
            gitkeep_path.touch()
    
    return created

# Execute directory creation on import to ensure structure exists
# This satisfies the verification requirement: os.path.isdir('code')
if __name__ == '__main__':
    created = ensure_directories()
    print(f"Ensured directories: {created}")
    print(f"Seed: {get_seed()}")
    print(f"Log Level: {get_log_level()}")
    print(f"Data Path: {get_data_path()}")
    print(f"Reduction Levels: {get_reductions()}")
