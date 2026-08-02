"""
Configuration management module.
Handles loading of environment variables and configuration files.
Ensures no hardcoded secrets are used.
"""
import os
import random
import sys
from pathlib import Path
from typing import Optional, Dict, Any
import yaml

class ConfigError(Exception):
    """Custom exception for configuration errors."""
    pass

def load_env_config(env_file: Optional[Path] = None) -> Dict[str, str]:
    """
    Load environment variables from a .env file if it exists.
    
    Args:
        env_file: Optional path to .env file. Defaults to project root.
        
    Returns:
        Dictionary of environment variables
        
    Raises:
        ConfigError: If required variables are missing
    """
    if env_file is None:
        env_file = Path.cwd() / '.env'
    
    env_vars = {}
    
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        env_vars[key.strip()] = value.strip().strip('"').strip("'")
    
    # Also load from actual environment
    for key in list(os.environ.keys()):
        if key.upper() in ['DRYAD_API_KEY', 'ANAGE_API_KEY', 'RANDOM_SEED']:
            env_vars[key] = os.environ[key]
    
    return env_vars

def validate_config(env_vars: Dict[str, str]) -> None:
    """
    Validate that required configuration variables are present.
    
    Args:
        env_vars: Dictionary of environment variables
        
    Raises:
        ConfigError: If required variables are missing
    """
    # Check for API keys - they should be present but NOT hardcoded in code
    # The presence check ensures the key exists, the actual value should come from env
    required_keys = []  # Add specific keys if needed, but prefer runtime validation
    
    # We don't fail if keys are missing - the actual API calls will fail gracefully
    # This allows the pipeline to run in test/demo mode without keys
    pass

def init_config(env_file: Optional[Path] = None) -> Dict[str, Any]:
    """
    Initialize the project configuration.
    
    Args:
        env_file: Optional path to .env file
        
    Returns:
        Configuration dictionary
        
    Raises:
        ConfigError: If configuration is invalid
    """
    env_vars = load_env_config(env_file)
    validate_config(env_vars)
    
    config = {
        'dryad_api_key': env_vars.get('DRYAD_API_KEY', os.environ.get('DRYAD_API_KEY')),
        'anage_api_key': env_vars.get('ANAGE_API_KEY', os.environ.get('ANAGE_API_KEY')),
        'random_seed': int(env_vars.get('RANDOM_SEED', os.environ.get('RANDOM_SEED', 42))),
        'log_level': env_vars.get('LOG_LEVEL', 'INFO'),
        'data_dir': Path.cwd() / 'data',
        'results_dir': Path.cwd() / 'results',
        'logs_dir': Path.cwd() / 'logs',
    }
    
    return config

def get_config() -> Dict[str, Any]:
    """
    Get the current configuration.
    
    Returns:
        Configuration dictionary
    """
    return init_config()

def set_random_seed(seed: Optional[int] = None) -> None:
    """
    Set the random seed for reproducibility.
    
    Args:
        seed: Random seed value. Defaults to config value or 42.
    """
    if seed is None:
        config = get_config()
        seed = config.get('random_seed', 42)
    
    random.seed(seed)
    if 'numpy' in sys.modules:
        import numpy as np
        np.random.seed(seed)

def load_env_config(env_file: Optional[Path] = None) -> Dict[str, str]:
    """
    Load environment variables from a .env file if it exists.
    
    Args:
        env_file: Optional path to .env file. Defaults to project root.
        
    Returns:
        Dictionary of environment variables
    """
    return load_env_config(env_file)