"""
Configuration management utilities for the plant root architecture prediction pipeline.

This module provides functions to load, validate, and access environment variables
and configuration settings.
"""
import os
from pathlib import Path
from typing import Optional, Dict, Any, List
import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class Config:
    """Configuration container class for project settings."""
    
    def __init__(self, **kwargs):
        """Initialize configuration from keyword arguments."""
        self._config = {}
        for key, value in kwargs.items():
            setattr(self, key, value)
            self._config[key] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value by key."""
        return getattr(self, key, default)
    
    def set(self, key: str, value: Any):
        """Set a configuration value."""
        setattr(self, key, value)
        self._config[key] = value
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return self._config.copy()
    
    def __repr__(self):
        return f"Config({self._config})"

def load_environment(env_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load environment variables from .env file and return as dictionary.
    
    Args:
        env_path: Optional path to .env file. If None, uses default location.
        
    Returns:
        Dictionary of environment variables
    """
    if env_path is None:
        # Default to .env in project root
        project_root = Path(__file__).resolve().parent.parent
        env_path = project_root / '.env'
    
    if env_path.exists():
        load_dotenv(env_path)
        logger.debug(f"Loaded environment from {env_path}")
    else:
        logger.warning(f"No .env file found at {env_path}, using system environment variables only")
    
    # Return all environment variables as a dictionary
    return dict(os.environ)

def get_env(var_name: str, default: Optional[str] = None, required: bool = False) -> Optional[str]:
    """
    Get an environment variable with optional default and validation.
    
    Args:
        var_name: Name of the environment variable
        default: Default value if variable is not set
        required: If True, raise error if variable is not set
        
    Returns:
        Value of the environment variable or default
        
    Raises:
        ValueError: If required=True and variable is not set
    """
    value = os.getenv(var_name, default)
    
    if required and value is None:
        raise ValueError(f"Required environment variable '{var_name}' is not set")
    
    return value

def get_config() -> Config:
    """
    Load configuration from environment variables and return as Config object.
    
    Returns:
        Config object with all configuration values
    """
    # Load environment first
    env_vars = load_environment()
    
    # Define type converters
    type_converters = {
        'RUN_MODE': str,
        'RANDOM_SEED': int,
        'LOG_LEVEL': str,
        'DATA_RAW_DIR': str,
        'DATA_PROCESSED_DIR': str,
        'DATA_LOGS_DIR': str,
        'FIGURES_DIR': str,
        'ARTIFACTS_DIR': str,
        'MODEL_TYPE': str,
        'N_ESTIMATORS': int,
        'MAX_DEPTH': lambda x: None if x.lower() == 'none' else int(x),
        'LOSO_ENABLED': lambda x: x.lower() in ('true', '1', 'yes'),
        'STRATIFIED_K_FOLD_ENABLED': lambda x: x.lower() in ('true', '1', 'yes'),
        'K_FOLD_K': int,
        'N_PERMUTATIONS': int,
        'PERMUTATION_SEED': int,
        'MIN_MATCH_PROPORTION': float,
        'MIN_OBSERVATIONS_PER_SPECIES': int,
        'SIGNIFICANCE_THRESHOLD': float,
    }
    
    config_dict = {}
    
    # Convert and set each configuration value
    for key, converter in type_converters.items():
        value = env_vars.get(key)
        if value is not None:
            try:
                config_dict[key] = converter(value)
            except (ValueError, TypeError) as e:
                logger.error(f"Failed to convert {key}='{value}': {e}")
                # Use default or skip
                continue
        else:
            # Try to set a reasonable default
            if key == 'RUN_MODE':
                config_dict[key] = 'production'
            elif key == 'RANDOM_SEED':
                config_dict[key] = 42
            elif key == 'LOG_LEVEL':
                config_dict[key] = 'INFO'
            elif key.endswith('_DIR'):
                config_dict[key] = key.lower().replace('_dir', '').replace('data_', 'data/')
            elif key == 'N_ESTIMATORS':
                config_dict[key] = 100
            elif key == 'K_FOLD_K':
                config_dict[key] = 5
            elif key == 'N_PERMUTATIONS':
                config_dict[key] = 100
            elif key == 'MIN_MATCH_PROPORTION':
                config_dict[key] = 0.90
            elif key == 'MIN_OBSERVATIONS_PER_SPECIES':
                config_dict[key] = 10
            elif key == 'SIGNIFICANCE_THRESHOLD':
                config_dict[key] = 0.05
            elif key.endswith('_ENABLED'):
                config_dict[key] = True
    
    return Config(**config_dict)

def validate_config(config: Config) -> bool:
    """
    Validate that configuration values are within acceptable ranges.
    
    Args:
        config: Config object to validate
        
    Returns:
        True if configuration is valid
        
    Raises:
        ValueError: If configuration is invalid
    """
    errors = []
    
    # Validate RUN_MODE
    if config.get('RUN_MODE') not in ['production', 'test']:
        errors.append(f"RUN_MODE must be 'production' or 'test', got '{config.get('RUN_MODE')}'")
    
    # Validate RANDOM_SEED
    if not isinstance(config.get('RANDOM_SEED'), int) or config.get('RANDOM_SEED') < 0:
        errors.append(f"RANDOM_SEED must be a non-negative integer")
    
    # Validate MIN_MATCH_PROPORTION
    min_match = config.get('MIN_MATCH_PROPORTION')
    if not isinstance(min_match, (int, float)) or not (0.0 <= min_match <= 1.0):
        errors.append(f"MIN_MATCH_PROPORTION must be between 0.0 and 1.0")
    
    # Validate MIN_OBSERVATIONS_PER_SPECIES
    min_obs = config.get('MIN_OBSERVATIONS_PER_SPECIES')
    if not isinstance(min_obs, int) or min_obs < 1:
        errors.append(f"MIN_OBSERVATIONS_PER_SPECIES must be a positive integer")
    
    if errors:
        raise ValueError("Configuration validation failed:\n" + "\n".join(errors))
    
    return True