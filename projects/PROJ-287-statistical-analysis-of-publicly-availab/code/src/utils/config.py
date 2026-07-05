"""
Configuration management module for the llmXive statistical analysis pipeline.

This module provides utilities for loading environment variables, managing
random seeds for reproducibility, and ensuring required directory structures exist.
"""

import os
import random
from pathlib import Path
from typing import Any, Dict, Optional, Type, TypeVar
import numpy as np

# Custom exception for configuration errors
class ConfigError(Exception):
    """Raised when configuration loading or validation fails."""
    pass

T = TypeVar('T')

def load_env_variable(
    name: str,
    default: Optional[str] = None,
    required: bool = False
) -> Optional[str]:
    """
    Load an environment variable with optional default and required flag.

    Args:
        name: The environment variable name.
        default: Default value if the variable is not set.
        required: If True, raises ConfigError if the variable is missing.

    Returns:
        The value of the environment variable or the default.

    Raises:
        ConfigError: If required is True and the variable is not set.
    """
    value = os.getenv(name, default)
    if required and value is None:
        raise ConfigError(f"Required environment variable '{name}' is not set.")
    return value

def get_random_seed(seed_name: str = "RANDOM_SEED") -> int:
    """
    Get a random seed from environment variables or generate one.

    This ensures reproducibility by allowing the seed to be set via
    environment variables while providing a fallback mechanism.

    Args:
        seed_name: The name of the environment variable to check for the seed.

    Returns:
        An integer random seed.
    """
    seed_str = load_env_variable(seed_name, default=None)
    if seed_str is not None:
        try:
            seed = int(seed_str)
        except ValueError:
            raise ConfigError(f"Invalid random seed value: '{seed_str}'. Must be an integer.")
    else:
        # Generate a random seed if not specified
        seed = random.randint(0, 2**31 - 1)
        # Log the generated seed for reproducibility tracking
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"No seed provided for '{seed_name}'. Generated new seed: {seed}")

    # Set seeds for all relevant libraries
    random.seed(seed)
    np.random.seed(seed)

    return seed

def get_config_dict() -> Dict[str, Any]:
    """
    Load all relevant configuration parameters into a dictionary.

    Returns:
        A dictionary containing configuration values.
    """
    config = {}

    # Data paths
    config['data_raw_dir'] = load_env_variable('DATA_RAW_DIR', 'data/raw')
    config['data_processed_dir'] = load_env_variable('DATA_PROCESSED_DIR', 'data/processed')
    config['results_dir'] = load_env_variable('RESULTS_DIR', 'results')
    config['figures_dir'] = load_env_variable('FIGURES_DIR', 'results/figures')
    config['stats_dir'] = load_env_variable('STATS_DIR', 'results/stats')

    # Analysis parameters
    config['min_tokens'] = int(load_env_variable('MIN_TOKENS', '20'))
    config['max_retries'] = int(load_env_variable('MAX_RETRIES', '3'))
    config['window_size'] = int(load_env_variable('WINDOW_SIZE', '5'))
    config['k_topics'] = int(load_env_variable('K_TOPICS', '10'))
    config['max_iter_lda'] = int(load_env_variable('MAX_ITER_LDA', '20'))
    config['coherence_threshold'] = float(load_env_variable('COHERENCE_THRESHOLD', '0.4'))
    config['permutation_iterations'] = int(load_env_variable('PERMUTATION_ITERATIONS', '1000'))
    config['permutation_sample_size'] = int(load_env_variable('PERMUTATION_SAMPLE_SIZE', '2000'))

    # Random seeds
    config['random_seed'] = get_random_seed()

    # API settings
    config['arxiv_email'] = load_env_variable('ARXIV_EMAIL', 'anonymous@example.com')
    config['pubmed_email'] = load_env_variable('PUBMED_EMAIL', 'anonymous@example.com')
    config['api_timeout'] = int(load_env_variable('API_TIMEOUT', '30'))

    return config

def ensure_directories(config: Optional[Dict[str, Any]] = None) -> None:
    """
    Ensure all required directories exist based on configuration.

    Args:
        config: Optional configuration dictionary. If None, loads default config.

    Raises:
        ConfigError: If a directory cannot be created.
    """
    if config is None:
        config = get_config_dict()

    directories = [
        config['data_raw_dir'],
        config['data_processed_dir'],
        config['results_dir'],
        config['figures_dir'],
        config['stats_dir']
    ]

    for dir_path in directories:
        path = Path(dir_path)
        try:
            path.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            raise ConfigError(f"Failed to create directory '{dir_path}': {e}")