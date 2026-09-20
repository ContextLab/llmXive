"""
Configuration management for the Doomscrolling Anxiety study.
Handles environment variables, seeds, and directory setup.
"""
import os
import random
import logging
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
import yaml

logger = logging.getLogger(__name__)

class ConfigError(Exception):
    """Custom exception for configuration errors."""
    pass

def load_config(config_path: str = 'config.yaml') -> Dict[str, Any]:
    """
    Loads configuration from a YAML file.

    Args:
        config_path: Path to the config file.

    Returns:
        Dict containing configuration.

    Raises:
        ConfigError: If file not found or invalid.
    """
    if not os.path.exists(config_path):
        # Default config if file missing
        logger.warning(f"Config file {config_path} not found. Using defaults.")
        return {
            'paths': {
                'raw_data': 'data/raw',
                'processed_data': 'data/processed',
                'outputs': 'outputs'
            },
            'dataset_url': os.getenv('DATASET_URL', 'https://example.com/data.csv'),
            'seed': None
        }
    
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        raise ConfigError(f"Failed to load config: {e}") from e

def set_seed(seed: Optional[int]) -> None:
    """
    Sets the random seed for reproducibility.

    Args:
        seed: The seed value.
    """
    if seed is not None:
        random.seed(seed)
        np.random.seed(seed) # Assuming numpy is used
        logger.info(f"Random seed set to: {seed}")
    else:
        logger.warning("No random seed provided. Results may not be reproducible.")

def verify_and_apply_seed(config: Dict[str, Any]) -> int:
    """
    Verifies seed exists in config and applies it.

    Args:
        config: Configuration dictionary.

    Returns:
        The seed value used.

    Raises:
        ValueError: If seed is missing.
    """
    seed = config.get('seed')
    if seed is None:
        raise ValueError("Seed is missing in configuration. Reproducibility cannot be guaranteed.")
    
    set_seed(seed)
    return seed

def log_seed_status(seed: Optional[int]) -> None:
    """
    Logs the status of the random seed.

    Args:
        seed: The seed value.
    """
    if seed is None:
        logger.warning("WARNING: Random seed not set. Execution is non-deterministic.")
    else:
        logger.info(f"INFO: Random seed set to {seed}.")

def get_dataset_url(config: Optional[Dict[str, Any]] = None) -> str:
    """
    Retrieves the dataset URL from config or environment.

    Args:
        config: Optional config dict.

    Returns:
        Dataset URL.
    """
    if config:
        return config.get('dataset_url', os.getenv('DATASET_URL', ''))
    return os.getenv('DATASET_URL', '')

def ensure_directories(config: Optional[Dict[str, Any]] = None) -> None:
    """
    Ensures all required directories exist.

    Args:
        config: Optional config dict.
    """
    if config is None:
        config = load_config()
    
    paths = config.get('paths', {})
    for key, path_str in paths.items():
        p = Path(path_str)
        p.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Ensured directory: {p}")

def main():
    """
    Main entry point for config verification.
    """
    config = load_config()
    try:
        seed = verify_and_apply_seed(config)
        log_seed_status(seed)
        ensure_directories(config)
        logger.info("Configuration verified and applied successfully.")
    except ValueError as e:
        logger.error(str(e))

if __name__ == '__main__':
    main()
