"""
Environment configuration management for reproducible research.

This module handles the setup and validation of PYTHONHASHSEED and random seeds
to ensure deterministic behavior across runs, which is critical for scientific
reproducibility in the social exclusion study pipeline.
"""

import os
import random
import sys
from pathlib import Path
from typing import Optional, Dict, Any

import numpy as np
import yaml

# Import existing logging infrastructure
from logging_config import get_project_logger


logger = get_project_logger("environment_config")


# Default configuration
DEFAULT_SEED = 42
DEFAULT_HASH_SEED = "42"


def load_environment_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load environment configuration from a YAML file or return defaults.

    Args:
        config_path: Path to the YAML configuration file. If None, looks for
                    'environment_config.yaml' in the project root.

    Returns:
        Dictionary containing seed configuration.
    """
    if config_path is None:
        config_path = Path(__file__).parent.parent / "environment_config.yaml"

    config_path = Path(config_path)

    if not config_path.exists():
        logger.warning(f"Config file {config_path} not found. Using defaults.")
        return {
            "random_seed": DEFAULT_SEED,
            "hash_seed": DEFAULT_HASH_SEED,
            "numpy_seed": DEFAULT_SEED,
            "pytorch_seed": None,  # Optional, only if torch is used
        }

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # Ensure required keys exist with defaults
    defaults = {
        "random_seed": DEFAULT_SEED,
        "hash_seed": DEFAULT_HASH_SEED,
        "numpy_seed": DEFAULT_SEED,
    }

    for key, value in defaults.items():
        if key not in config:
            config[key] = value

    return config


def set_python_hash_seed(seed_value: Optional[str] = None) -> None:
    """
    Set the PYTHONHASHSEED environment variable for deterministic hashing.

    This must be called BEFORE any hashing operations occur (ideally at module load).
    Setting this after imports may not have the desired effect.

    Args:
        seed_value: The hash seed value as a string. If None, uses config default.
    """
    if seed_value is None:
        config = load_environment_config()
        seed_value = str(config.get("hash_seed", DEFAULT_HASH_SEED))

    # Only set if not already set or if explicitly requested
    if "PYTHONHASHSEED" not in os.environ or seed_value:
        os.environ["PYTHONHASHSEED"] = str(seed_value)
        logger.info(f"Set PYTHONHASHSEED to {seed_value}")
    else:
        logger.info(f"PYTHONHASHSEED already set to {os.environ['PYTHONHASHSEED']}")


def set_random_seeds(config: Optional[Dict[str, Any]] = None) -> None:
    """
    Set random seeds for Python's random module, NumPy, and optionally PyTorch.

    This ensures reproducible randomness across all libraries used in the pipeline.

    Args:
        config: Optional configuration dictionary. If None, loads from config file.
    """
    if config is None:
        config = load_environment_config()

    # Get seeds from config
    random_seed = config.get("random_seed", DEFAULT_SEED)
    numpy_seed = config.get("numpy_seed", random_seed)

    # Set Python's random seed
    random.seed(random_seed)
    logger.info(f"Set Python random seed to {random_seed}")

    # Set NumPy seed
    np.random.seed(numpy_seed)
    logger.info(f"Set NumPy random seed to {numpy_seed}")

    # Attempt to set PyTorch seed if available (optional)
    try:
        import torch
        torch.manual_seed(random_seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(random_seed)
        logger.info(f"Set PyTorch random seed to {random_seed}")
    except ImportError:
        logger.debug("PyTorch not installed, skipping PyTorch seed setup")


def validate_seed_environment() -> bool:
    """
    Validate that the environment is properly configured for reproducibility.

    Returns:
        True if environment is valid, False otherwise.
    """
    is_valid = True

    # Check PYTHONHASHSEED
    hash_seed = os.environ.get("PYTHONHASHSEED")
    if hash_seed is None:
        logger.warning("PYTHONHASHSEED is not set. Results may be non-deterministic.")
        is_valid = False
    else:
        logger.info(f"PYTHONHASHSEED is set to {hash_seed}")

    # Check random module
    try:
        # Try to generate a number and see if it's consistent
        val1 = random.random()
        random.seed(42)
        val2 = random.random()
        if val1 == val2:
            logger.debug("Random seed appears to be working correctly")
        else:
            logger.debug("Random seed behavior noted (expected if not reset)")
    except Exception as e:
        logger.error(f"Error validating random module: {e}")
        is_valid = False

    return is_valid


def initialize_environment(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Initialize the entire environment for reproducible research.

    This function should be called at the very beginning of the pipeline execution,
    before any other imports or operations that might depend on randomness or hashing.

    Args:
        config_path: Path to the environment configuration YAML file.

    Returns:
        The loaded configuration dictionary.
    """
    logger.info("Initializing environment for reproducible research...")

    # Load configuration
    config = load_environment_config(config_path)

    # Set PYTHONHASHSEED first (critical for determinism)
    set_python_hash_seed(config.get("hash_seed"))

    # Set random seeds
    set_random_seeds(config)

    # Validate environment
    if not validate_seed_environment():
        logger.warning("Environment validation completed with warnings. "
                     "Consider setting PYTHONHASHSEED for full reproducibility.")
    else:
        logger.info("Environment validation passed.")

    logger.info(f"Environment initialized with seed: {config.get('random_seed')}")
    return config


def create_default_config_file(output_path: Optional[str] = None) -> Path:
    """
    Create a default environment configuration file.

    Args:
        output_path: Path where the config file should be created. If None,
                    creates 'environment_config.yaml' in the project root.

    Returns:
        Path to the created configuration file.
    """
    if output_path is None:
        output_path = Path(__file__).parent.parent / "environment_config.yaml"

    output_path = Path(output_path)

    default_config = {
        "random_seed": DEFAULT_SEED,
        "hash_seed": DEFAULT_HASH_SEED,
        "numpy_seed": DEFAULT_SEED,
        "description": "Configuration for reproducible research in social exclusion study.",
        "notes": [
            "Set PYTHONHASHSEED for deterministic dictionary ordering.",
            "All random seeds are set at pipeline initialization.",
            "Change seeds to generate different random variations if needed."
        ]
    }

    with open(output_path, "w", encoding="utf-8") as f:
        yaml.dump(default_config, f, default_flow_style=False, sort_keys=False)

    logger.info(f"Created default configuration file at {output_path}")
    return output_path


# Convenience function for quick initialization
def init():
    """
    Quick initialization of the environment with default settings.
    Equivalent to calling initialize_environment() with no arguments.
    """
    return initialize_environment()
