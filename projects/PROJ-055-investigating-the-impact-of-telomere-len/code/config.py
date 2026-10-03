import os
import random
import sys
from pathlib import Path
from typing import Optional, Dict, Any
import yaml

class ConfigError(Exception):
    """Custom exception for configuration errors."""
    pass

def load_env_config(env_path: Optional[Path] = None) -> Dict[str, str]:
    """
    Loads environment variables from a .env file or the current environment.
    
    Args:
        env_path: Path to the .env file. If None, looks for .env in the project root.
    
    Returns:
        Dictionary of environment variables.
    """
    if env_path is None:
        # Default to project root .env
        project_root = Path(__file__).parent.parent
        env_path = project_root / ".env"
    
    config = {}
    
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        config[key.strip()] = value.strip()
    
    # Override with actual environment variables if set
    for key in list(config.keys()):
        if key in os.environ:
            config[key] = os.environ[key]
    
    return config

def validate_config(config: Dict[str, str]) -> None:
    """
    Validates the configuration dictionary for required keys.
    
    Raises:
        ConfigError: If required keys are missing or invalid.
    """
    # Define required keys
    required_keys = ['RANDOM_SEED']
    
    missing_keys = [key for key in required_keys if key not in config or not config[key]]
    if missing_keys:
        raise ConfigError(f"Missing required configuration keys: {', '.join(missing_keys)}")
    
    # Validate RANDOM_SEED is an integer
    try:
        seed = int(config['RANDOM_SEED'])
    except ValueError:
        raise ConfigError(f"RANDOM_SEED must be an integer, got: {config['RANDOM_SEED']}")

def init_config(env_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Initializes the configuration by loading and validating environment settings.
    
    Args:
        env_path: Path to the .env file.
    
    Returns:
        Dictionary containing validated configuration values.
    """
    config = load_env_config(env_path)
    validate_config(config)
    return config

def get_config() -> Dict[str, Any]:
    """
    Retrieves the current project configuration.
    Initializes if not already loaded.
    
    Returns:
        Dictionary containing configuration values.
    """
    # Use a simple global cache or re-load based on project needs
    # For this implementation, we load fresh to ensure .env changes are picked up
    # In a production system, a singleton pattern might be preferred
    return init_config()

def set_random_seed(seed: Optional[int] = None) -> int:
    """
    Sets the random seed for reproducibility across the pipeline.
    
    Args:
        seed: The seed value. If None, reads from configuration.
    
    Returns:
        The seed value used.
    """
    if seed is None:
        config = get_config()
        seed = int(config['RANDOM_SEED'])
    
    random.seed(seed)
    # Also set numpy seed if available, as many data scripts use it
    try:
        import numpy as np
        np.random.seed(seed)
    except ImportError:
        pass
    
    return seed
