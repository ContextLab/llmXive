"""
Configuration management for the EBSD data pipeline.

This module provides centralized configuration loading from environment variables
and configuration files, with strict validation and error handling.
"""
import os
from typing import List, Optional
from pathlib import Path

class ConfigurationError(Exception):
    """Custom exception for configuration-related errors."""
    pass


def get_reductions() -> List[float]:
    """
    Get the list of cold-rolling reduction levels from configuration.
    
    Reduction levels are read from the REDUCTION_LEVELS environment variable
    as a comma-separated list of floats.
    
    Returns:
        List of reduction levels (e.g., [0.1, 0.2, 0.3, 0.5])
        
    Raises:
        ConfigurationError: If REDUCTION_LEVELS is not set or is empty
    """
    reduction_str = os.environ.get('REDUCTION_LEVELS')
    
    if not reduction_str:
        raise ConfigurationError(
            "REDUCTION_LEVELS environment variable is not set. "
            "Please set it to a comma-separated list of reduction levels (e.g., '0.1,0.2,0.3')."
        )
    
    try:
        reductions = [float(x.strip()) for x in reduction_str.split(',') if x.strip()]
    except ValueError as e:
        raise ConfigurationError(
            f"Invalid format for REDUCTION_LEVELS: {reduction_str}. "
            f"Expected comma-separated floats. Error: {e}"
        )
    
    if not reductions:
        raise ConfigurationError(
            "REDUCTION_LEVELS is empty after parsing. "
            "Please provide at least one valid reduction level."
        )
    
    return reductions


def get_seed() -> int:
    """
    Get the random seed for reproducible experiments.
    
    Returns:
        Random seed as an integer. Defaults to 42 if not set.
    """
    seed_str = os.environ.get('RANDOM_SEED', '42')
    try:
        return int(seed_str)
    except ValueError:
        raise ConfigurationError(
            f"Invalid RANDOM_SEED value: {seed_str}. Expected an integer."
        )


def get_data_path() -> Path:
    """
    Get the base path for data directories.
    
    Returns:
        Path to the data directory. Defaults to 'data' in current working directory.
    """
    data_path_str = os.environ.get('DATA_PATH', 'data')
    return Path(data_path_str).resolve()


def get_log_level() -> int:
    """
    Get the logging level from configuration.
    
    Returns:
        Logging level constant (e.g., logging.INFO, logging.DEBUG).
    """
    log_level_str = os.environ.get('LOG_LEVEL', 'INFO').upper()
    
    level_map = {
        'DEBUG': 10,
        'INFO': 20,
        'WARNING': 30,
        'ERROR': 40,
        'CRITICAL': 50
    }
    
    if log_level_str not in level_map:
        raise ConfigurationError(
            f"Invalid LOG_LEVEL: {log_level_str}. "
            f"Must be one of: {list(level_map.keys())}"
        )
    
    return level_map[log_level_str]