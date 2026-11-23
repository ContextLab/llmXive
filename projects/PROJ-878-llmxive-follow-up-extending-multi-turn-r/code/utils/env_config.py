"""
Helper utilities for environment configuration management.
Provides validation and helper functions for environment variables.
"""
import os
from typing import Optional, List
import logging

REQUIRED_VARS = [
    "RANDOM_SEED",
    "MODEL_PATH",
    "MAX_TURNS",
    "DATA_PATH_RAW",
    "DATA_PATH_PROCESSED",
    "RESULTS_PATH",
]

def validate_environment() -> List[str]:
    """
    Check that all required environment variables are set.
    
    Returns:
        List of missing variable names. Empty if all are present.
    """
    missing = []
    for var in REQUIRED_VARS:
        if var not in os.environ:
            missing.append(var)
    return missing

def get_required_var(var_name: str, default: Optional[str] = None) -> str:
    """
    Get a required environment variable with optional default.
    
    Args:
        var_name: Name of the environment variable.
        default: Default value if not set (optional).
    
    Returns:
        The value of the environment variable.
    
    Raises:
        ValueError: If the variable is not set and no default provided.
    """
    value = os.environ.get(var_name)
    if value is None:
        if default is not None:
            value = default
            logging.warning(f"Environment variable {var_name} not set, using default: {default}")
        else:
            raise ValueError(f"Required environment variable {var_name} is not set")
    return value

def get_int_var(var_name: str, default: Optional[int] = None) -> int:
    """
    Get an environment variable as an integer.
    
    Args:
        var_name: Name of the environment variable.
        default: Default value if not set.
    
    Returns:
        The integer value.
    
    Raises:
        ValueError: If conversion fails.
    """
    value = get_required_var(var_name, str(default) if default is not None else None)
    try:
        return int(value)
    except ValueError:
        raise ValueError(f"Environment variable {var_name} must be an integer, got: {value}")
