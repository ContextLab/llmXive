"""
Configuration utilities for llmXive.

This module provides seed pinning, path configuration, and environment variable handling.
"""
import os
import random
from pathlib import Path
from typing import Optional, Dict, Any

import numpy as np

def set_seed(seed: int = 42) -> None:
    """
    Set random seeds for reproducibility.

    Args:
        seed: Random seed value.
    """
    random.seed(seed)
    np.random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)

def get_project_root() -> Path:
    """
    Get the project root directory.

    Returns:
        Path: Path to the project root.
    """
    return Path(__file__).parent.parent.parent

def get_data_dir() -> Path:
    """
    Get the data directory path.

    Returns:
        Path: Path to the data directory.
    """
    return get_project_root() / "data"

def get_code_dir() -> Path:
    """
    Get the code directory path.

    Returns:
        Path: Path to the code directory.
    """
    return get_project_root() / "code"

def get_env_variable(name: str, default: Optional[str] = None, required: bool = False) -> str:
    """
    Get an environment variable with optional default and required flag.

    Args:
        name: Environment variable name.
        default: Default value if not set.
        required: Whether the variable is required.

    Returns:
        str: Value of the environment variable.

    Raises:
        ValueError: If required and not set.
    """
    value = os.environ.get(name, default)
    if required and value is None:
        raise ValueError(f"Required environment variable '{name}' is not set")
    return value

def load_config_from_env(prefix: str = "LLMXIVE_") -> Dict[str, Any]:
    """
    Load configuration from environment variables with a specific prefix.

    Args:
        prefix: Prefix for environment variables.

    Returns:
        dict: Dictionary of configuration values.
    """
    config = {}
    for key, value in os.environ.items():
        if key.startswith(prefix):
            config_key = key[len(prefix):].lower()
            # Try to convert to appropriate type
            if value.lower() in ('true', 'false'):
                config[config_key] = value.lower() == 'true'
            elif value.isdigit():
                config[config_key] = int(value)
            elif value.replace('.', '', 1).isdigit():
                config[config_key] = float(value)
            else:
                config[config_key] = value
    return config