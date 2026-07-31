"""
Configuration module for the project.

Handles environment variables, seed management, and reduction levels.
"""

import os
from typing import List, Optional
from pathlib import Path

class ConfigurationError(Exception):
    """Custom exception for configuration errors."""
    pass

def get_reductions() -> List[float]:
    """
    Get the list of cold rolling reduction levels from configuration.

    Returns
    -------
    List[float]
        List of reduction percentages (e.g., [30, 50, 70]).

    Raises
    ------
    ConfigurationError
        If reduction levels are not defined in configuration.
    """
    # Try to get from environment variable first
    env_reductions = os.getenv("COLD_ROLLING_REDUCTIONS")
    
    if env_reductions:
        try:
            reductions = [float(x.strip()) for x in env_reductions.split(",")]
            if not reductions:
                raise ConfigurationError("COLD_ROLLING_REDUCTIONS is empty")
            return reductions
        except ValueError as e:
            raise ConfigurationError(f"Invalid reduction values in environment: {e}")
    
    # Fallback to default if not set (for testing/development)
    # In production, this should be explicitly configured
    default_reductions = [30.0, 50.0, 70.0]
    
    # Check if we're in a test environment
    if os.getenv("TESTING") == "true":
        return default_reductions
    
    # If not in test mode and not configured, raise error
    # This ensures fail-fast behavior as required by FR-002
    raise ConfigurationError(
        "Cold rolling reduction levels not configured. "
        "Set COLD_ROLLING_REDUCTIONS environment variable (e.g., '30,50,70') "
        "or set TESTING=true for development."
    )

def get_seed() -> int:
    """
    Get the random seed for reproducibility.

    Returns
    -------
    int
        Random seed value.

    Defaults to 42 if not specified.
    """
    seed_str = os.getenv("RANDOM_SEED", "42")
    try:
        return int(seed_str)
    except ValueError:
        return 42  # Fallback to default

def get_data_path() -> Path:
    """
    Get the base data directory path.

    Returns
    -------
    Path
        Path to the data directory.
    """
    data_path = os.getenv("DATA_PATH", "data")
    return Path(data_path)

def get_log_level() -> str:
    """
    Get the logging level from configuration.

    Returns
    -------
    str
        Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
    """
    return os.getenv("LOG_LEVEL", "INFO")

# Validate configuration on import if not in test mode
if os.getenv("TESTING") != "true":
    try:
        _ = get_reductions()
    except ConfigurationError:
        # Log warning but don't fail import (import time validation)
        import logging
        logging.warning("Configuration warning: Reduction levels not set. "
                      "Will fail on first use if not configured.")
