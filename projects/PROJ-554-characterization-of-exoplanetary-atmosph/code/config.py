"""
Configuration management for the exoplanetary atmosphere characterization pipeline.
Handles environment variables, random seeds, and path configuration.
"""
import os
import random
import logging
from pathlib import Path
from typing import Optional, Dict, Any
import numpy as np

logger = logging.getLogger(__name__)

class ConfigurationError(Exception):
    """Custom exception for configuration errors."""
    pass

def load_env_vars() -> Dict[str, str]:
    """Load environment variables relevant to the pipeline."""
    # Example: Load API keys or specific paths from env
    env_vars = {
        'DATA_DIR': os.getenv('DATA_DIR', 'data'),
        'RESULTS_DIR': os.getenv('RESULTS_DIR', 'results'),
        'LOG_LEVEL': os.getenv('LOG_LEVEL', 'INFO'),
    }
    return env_vars

def set_random_seed(seed: int = 42) -> None:
    """Set random seeds for reproducibility across libraries."""
    random.seed(seed)
    np.random.seed(seed)
    logger.info(f"Random seed set to {seed}")

def get_config() -> Dict[str, Any]:
    """
    Get the full configuration dictionary.
    Merges environment variables with defaults.
    """
    env = load_env_vars()
    set_random_seed(42)

    config = {
        'paths': {
            'data_raw': Path(env['DATA_DIR']) / 'raw',
            'data_processed': Path(env['DATA_DIR']) / 'processed',
            'results': Path(env['RESULTS_DIR']),
            'figures': Path(env['RESULTS_DIR']) / 'plots',
        },
        'analysis': {
            'bootstrap_iterations': 1000,
            'snr_threshold': 5.0,
            'random_seed': 42,
        },
        'logging': {
            'level': env['LOG_LEVEL'],
        }
    }

    # Ensure directories exist
    for path in config['paths'].values():
        path.mkdir(parents=True, exist_ok=True)

    return config

def validate_config(config: Dict[str, Any]) -> bool:
    """Validate that the configuration is complete and paths are valid."""
    required_keys = ['paths', 'analysis']
    for key in required_keys:
        if key not in config:
            raise ConfigurationError(f"Missing required config key: {key}")

    # Check path existence (for read paths)
    # (Write paths are created in get_config)
    return True

def main():
    """Main entry point for config testing."""
    config = get_config()
    print(f"Configuration loaded: {config}")
    validate_config(config)
    print("Configuration validated successfully.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
