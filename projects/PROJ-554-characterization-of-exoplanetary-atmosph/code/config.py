"""
Configuration management for the Exoplanetary Atmosphere Characterization pipeline.

This module handles:
- Loading environment variables (API keys, paths)
- Setting random seeds for reproducibility
- Validating configuration integrity
"""
import os
import random
import logging
from pathlib import Path
from typing import Optional, Dict, Any

import numpy as np

# Configure logging for the module
logger = logging.getLogger(__name__)

# Default configuration values
DEFAULT_SEED = 42
DEFAULT_CPU_THREADS = 4
DEFAULT_MEMORY_LIMIT_GB = 8.0
DEFAULT_DATA_DIR = Path("data")
DEFAULT_RESULTS_DIR = Path("results")
DEFAULT_CODE_DIR = Path("code")

# Environment variable names
ENV_SEED = "EXOPLANET_SEED"
ENV_CPU_THREADS = "EXOPLANET_CPU_THREADS"
ENV_MEMORY_LIMIT = "EXOPLANET_MEMORY_LIMIT_GB"
ENV_NASA_API_KEY = "NASA_EXOPLANET_API_KEY"  # If API key is required in future
ENV_DATA_DIR = "EXOPLANET_DATA_DIR"
ENV_RESULTS_DIR = "EXOPLANET_RESULTS_DIR"
ENV_LOG_LEVEL = "EXOPLANET_LOG_LEVEL"

# Global configuration store
_config: Optional[Dict[str, Any]] = None


def load_env_vars() -> Dict[str, Any]:
    """
    Load configuration from environment variables.

    Returns:
        Dict containing loaded environment variables with defaults applied.
    """
    config = {}

    # Random Seed
    seed_str = os.getenv(ENV_SEED)
    if seed_str:
        try:
            config["seed"] = int(seed_str)
            logger.info(f"Loaded random seed from environment: {config['seed']}")
        except ValueError:
            logger.warning(f"Invalid seed value '{seed_str}', using default: {DEFAULT_SEED}")
            config["seed"] = DEFAULT_SEED
    else:
        config["seed"] = DEFAULT_SEED

    # CPU Threads
    threads_str = os.getenv(ENV_CPU_THREADS)
    if threads_str:
        try:
            config["cpu_threads"] = int(threads_str)
            logger.info(f"Loaded CPU threads from environment: {config['cpu_threads']}")
        except ValueError:
            logger.warning(f"Invalid CPU threads value '{threads_str}', using default: {DEFAULT_CPU_THREADS}")
            config["cpu_threads"] = DEFAULT_CPU_THREADS
    else:
        config["cpu_threads"] = DEFAULT_CPU_THREADS

    # Memory Limit
    mem_str = os.getenv(ENV_MEMORY_LIMIT)
    if mem_str:
        try:
            config["memory_limit_gb"] = float(mem_str)
            logger.info(f"Loaded memory limit from environment: {config['memory_limit_gb']} GB")
        except ValueError:
            logger.warning(f"Invalid memory limit '{mem_str}', using default: {DEFAULT_MEMORY_LIMIT_GB}")
            config["memory_limit_gb"] = DEFAULT_MEMORY_LIMIT_GB
    else:
        config["memory_limit_gb"] = DEFAULT_MEMORY_LIMIT_GB

    # Paths
    config["data_dir"] = Path(os.getenv(ENV_DATA_DIR, DEFAULT_DATA_DIR))
    config["results_dir"] = Path(os.getenv(ENV_RESULTS_DIR, DEFAULT_RESULTS_DIR))

    # API Keys (if needed)
    if os.getenv(ENV_NASA_API_KEY):
        logger.info("NASA Exoplanet API Key found in environment.")
        # Do not log the actual key value
    else:
        logger.debug("No NASA Exoplanet API Key found. Some endpoints may require authentication.")

    # Log Level
    log_level_str = os.getenv(ENV_LOG_LEVEL, "INFO").upper()
    if log_level_str in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"):
        config["log_level"] = log_level_str
    else:
        config["log_level"] = "INFO"

    return config


def set_random_seed(seed: Optional[int] = None) -> None:
    """
    Set random seeds for reproducibility across Python, NumPy, and random modules.

    Args:
        seed: Optional seed value. If None, uses the global config seed.
    """
    if seed is None:
        cfg = get_config()
        seed = cfg.get("seed", DEFAULT_SEED)

    random.seed(seed)
    np.random.seed(seed)
    logger.info(f"Random seeds set to: {seed}")


def get_config() -> Dict[str, Any]:
    """
    Get the current configuration. Loads it if not already loaded.

    Returns:
        The configuration dictionary.
    """
    global _config
    if _config is None:
        _config = load_env_vars()
        # Ensure seeds are set immediately upon config load for reproducibility
        set_random_seed(_config.get("seed"))
    return _config


def validate_config(config: Optional[Dict[str, Any]] = None) -> bool:
    """
    Validate the current configuration for critical errors.

    Args:
        config: Optional config dict to validate. If None, uses global config.

    Returns:
        True if valid, raises ConfigurationError if invalid.
    """
    if config is None:
        config = get_config()

    errors = []

    # Check paths exist or can be created
    data_dir = config.get("data_dir")
    if not isinstance(data_dir, Path):
        errors.append(f"data_dir must be a Path object, got {type(data_dir)}")
    elif not data_dir.exists() and not data_dir.is_dir():
        # Allow creation, but warn if parent doesn't exist
        if not data_dir.parent.exists():
            errors.append(f"Parent directory for data_dir does not exist: {data_dir.parent}")

    results_dir = config.get("results_dir")
    if not isinstance(results_dir, Path):
        errors.append(f"results_dir must be a Path object, got {type(results_dir)}")

    # Check numeric constraints
    threads = config.get("cpu_threads", 1)
    if not isinstance(threads, int) or threads < 1:
        errors.append(f"cpu_threads must be a positive integer, got {threads}")

    memory = config.get("memory_limit_gb", 1.0)
    if not isinstance(memory, (int, float)) or memory <= 0:
        errors.append(f"memory_limit_gb must be a positive number, got {memory}")

    if errors:
        error_msg = "Configuration validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
        raise ConfigurationError(error_msg)

    logger.info("Configuration validation passed.")
    return True


class ConfigurationError(Exception):
    """Custom exception for configuration errors."""
    pass


def main() -> None:
    """
    Main entry point for testing configuration loading.
    """
    try:
        logger.info("Starting configuration test...")
        cfg = get_config()
        logger.info(f"Loaded configuration: {cfg}")
        validate_config(cfg)
        logger.info("Configuration is valid.")
    except ConfigurationError as e:
        logger.error(f"Configuration error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during config test: {e}")
        raise