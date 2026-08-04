"""
Configuration management for the exoplanetary atmosphere characterization pipeline.
Handles environment variable loading, API key retrieval, and random seed setting
for reproducible research.
"""

import os
import random
import logging
from pathlib import Path
from typing import Optional, Dict, Any
import numpy as np

# Configure logging for this module
logger = logging.getLogger(__name__)

# Default configuration values
DEFAULT_SEED = 42
DEFAULT_CPU_THREADS = 4
DEFAULT_MEMORY_LIMIT_GB = 14.0

# Environment variable names for API keys
API_KEY_VARS = {
    'NASA_EXOPLANET_ARCHIVE': 'NASA_EXOPLANET_ARCHIVE_KEY',
    'HETDEX_API': 'HETDEX_API_KEY',
    'ESO_API': 'ESO_API_KEY',
}

def load_env_vars() -> Dict[str, Optional[str]]:
    """
    Load environment variables for API keys and configuration.
    
    Returns:
        Dict mapping variable names to their values (or None if not set).
    
    Raises:
        ConfigurationError: If critical API keys are missing when required.
    """
    env_vars = {}
    
    # Load API keys
    for service, var_name in API_KEY_VARS.items():
        value = os.getenv(var_name)
        env_vars[var_name] = value
        if value is None:
            logger.warning(f"API key environment variable {var_name} is not set. "
                         f"Service {service} may be unavailable.")
        else:
            logger.info(f"API key for {service} loaded from environment.")
    
    # Load configuration environment variables
    config_vars = [
        ('PIPELINE_SEED', 'PIPELINE_SEED'),
        ('CPU_THREADS', 'CPU_THREADS'),
        ('MEMORY_LIMIT_GB', 'MEMORY_LIMIT_GB'),
        ('DATA_DIR', 'DATA_DIR'),
        ('RESULTS_DIR', 'RESULTS_DIR'),
    ]
    
    for env_name, config_name in config_vars:
        value = os.getenv(env_name)
        env_vars[env_name] = value
        if value is not None:
            logger.info(f"Configuration {env_name} loaded from environment: {value}")
    
    return env_vars

def set_random_seed(seed: Optional[int] = None) -> int:
    """
    Set random seeds for reproducibility across all libraries.
    
    Args:
        seed: The random seed to use. If None, uses DEFAULT_SEED or
             the value from PIPELINE_SEED environment variable.
    
    Returns:
        The seed value that was set.
    
    Raises:
        ValueError: If the seed is negative or not an integer.
    """
    if seed is None:
        # Try to get from environment first
        env_seed = os.getenv('PIPELINE_SEED')
        if env_seed is not None:
            try:
                seed = int(env_seed)
            except ValueError:
                logger.warning(f"Invalid PIPELINE_SEED value '{env_seed}', using default {DEFAULT_SEED}")
                seed = DEFAULT_SEED
        else:
            seed = DEFAULT_SEED
    
    # Validate seed
    if not isinstance(seed, int):
        raise ValueError(f"Seed must be an integer, got {type(seed)}")
    if seed < 0:
        raise ValueError(f"Seed must be non-negative, got {seed}")
    
    # Set seeds for all relevant libraries
    random.seed(seed)
    np.random.seed(seed)
    
    # Set PYTHONHASHSEED for hash reproducibility
    os.environ['PYTHONHASHSEED'] = str(seed)
    
    logger.info(f"Random seed set to {seed} for reproducibility")
    return seed

def get_config() -> Dict[str, Any]:
    """
    Get the complete configuration dictionary.
    
    Returns:
        Dictionary containing all configuration values including:
        - api_keys: Dict of API key names to values
        - seed: Random seed value
        - cpu_threads: Number of CPU threads to use
        - memory_limit_gb: Memory limit in GB
        - data_dir: Path to data directory
        - results_dir: Path to results directory
    """
    # Load environment variables
    env_vars = load_env_vars()
    
    # Extract API keys
    api_keys = {
        service: env_vars.get(var_name)
        for service, var_name in API_KEY_VARS.items()
    }
    
    # Extract configuration values
    seed = None
    if env_vars.get('PIPELINE_SEED') is not None:
        try:
            seed = int(env_vars['PIPELINE_SEED'])
        except ValueError:
            seed = DEFAULT_SEED
    else:
        seed = DEFAULT_SEED
    
    cpu_threads = DEFAULT_CPU_THREADS
    if env_vars.get('CPU_THREADS') is not None:
        try:
            cpu_threads = int(env_vars['CPU_THREADS'])
        except ValueError:
            logger.warning(f"Invalid CPU_THREADS value, using default {DEFAULT_CPU_THREADS}")
    
    memory_limit_gb = DEFAULT_MEMORY_LIMIT_GB
    if env_vars.get('MEMORY_LIMIT_GB') is not None:
        try:
            memory_limit_gb = float(env_vars['MEMORY_LIMIT_GB'])
        except ValueError:
            logger.warning(f"Invalid MEMORY_LIMIT_GB value, using default {DEFAULT_MEMORY_LIMIT_GB}")
    
    data_dir = os.getenv('DATA_DIR', 'data')
    results_dir = os.getenv('RESULTS_DIR', 'results')
    
    config = {
        'api_keys': api_keys,
        'seed': seed,
        'cpu_threads': cpu_threads,
        'memory_limit_gb': memory_limit_gb,
        'data_dir': Path(data_dir),
        'results_dir': Path(results_dir),
    }
    
    return config

def validate_config(config: Dict[str, Any]) -> bool:
    """
    Validate the configuration dictionary.
    
    Args:
        config: Configuration dictionary to validate
    
    Returns:
        True if configuration is valid
    
    Raises:
        ConfigurationError: If configuration is invalid
    """
    from utils import ConfigurationError
    
    # Check required keys
    required_keys = ['api_keys', 'seed', 'cpu_threads', 'memory_limit_gb', 'data_dir', 'results_dir']
    for key in required_keys:
        if key not in config:
            raise ConfigurationError(f"Missing required configuration key: {key}")
    
    # Validate seed
    if not isinstance(config['seed'], int) or config['seed'] < 0:
        raise ConfigurationError(f"Invalid seed value: {config['seed']}")
    
    # Validate CPU threads
    if not isinstance(config['cpu_threads'], int) or config['cpu_threads'] < 1:
        raise ConfigurationError(f"Invalid CPU threads value: {config['cpu_threads']}")
    
    # Validate memory limit
    if not isinstance(config['memory_limit_gb'], (int, float)) or config['memory_limit_gb'] <= 0:
        raise ConfigurationError(f"Invalid memory limit value: {config['memory_limit_gb']}")
    
    # Validate directories
    if not isinstance(config['data_dir'], Path):
        config['data_dir'] = Path(config['data_dir'])
    if not isinstance(config['results_dir'], Path):
        config['results_dir'] = Path(config['results_dir'])
    
    if not config['data_dir'].is_absolute():
        config['data_dir'] = Path.cwd() / config['data_dir']
    if not config['results_dir'].is_absolute():
        config['results_dir'] = Path.cwd() / config['results_dir']
    
    logger.info("Configuration validated successfully")
    return True

def main():
    """
    Main function to demonstrate configuration loading and validation.
    """
    print("Loading configuration...")
    config = get_config()
    
    print(f"Random seed: {config['seed']}")
    print(f"CPU threads: {config['cpu_threads']}")
    print(f"Memory limit: {config['memory_limit_gb']} GB")
    print(f"Data directory: {config['data_dir']}")
    print(f"Results directory: {config['results_dir']}")
    
    print("\nAPI Keys:")
    for service, key in config['api_keys'].items():
        if key is not None:
            print(f"  {service}: [REDACTED]")
        else:
            print(f"  {service}: [NOT SET]")
    
    print("\nValidating configuration...")
    try:
        validate_config(config)
        print("Configuration is valid!")
    except Exception as e:
        print(f"Configuration validation failed: {e}")
        return 1
    
    return 0

if __name__ == '__main__':
    exit(main())