"""
Configuration management for the Exoplanet Atmospheric Characterization pipeline.

Handles environment variable loading for API keys, random seed initialization,
and project path resolution to ensure reproducibility and correct file I/O.
"""

import os
import random
import logging
from pathlib import Path
from typing import Optional, Dict, Any

# Configure logging for this module
logger = logging.getLogger(__name__)

# Default random seed for reproducibility
DEFAULT_SEED = 42

# Default API keys (None if not set in environment)
DEFAULT_API_KEYS = {
    "NASA_EXOPLANET_ARCHIVE_API_KEY": None,
    "SIMBAD_API_KEY": None,
    "VIZIER_API_KEY": None,
}

# Default hardware constraints
DEFAULT_CPU_THREADS = 4
DEFAULT_MEMORY_LIMIT_GB = 16.0


def load_env_vars() -> Dict[str, Optional[str]]:
    """
    Load API keys and configuration from environment variables.

    Returns a dictionary of key-value pairs where values are None if the
    environment variable is not set.

    Returns:
        Dict[str, Optional[str]]: Mapping of config key to value.
    """
    config = {}
    for key, default in DEFAULT_API_KEYS.items():
        value = os.getenv(key)
        config[key] = value
        if value is None:
            logger.warning(f"Environment variable {key} is not set. "
                           f"Using default: {default}")
        else:
            logger.info(f"Loaded environment variable: {key}")
    return config


def set_random_seed(seed: Optional[int] = None) -> int:
    """
    Initialize random seeds for reproducibility.

    Sets seeds for Python's built-in random module, NumPy, and optionally
    other libraries if available (e.g., torch, tensorflow).

    Args:
        seed: The random seed to use. If None, uses DEFAULT_SEED.

    Returns:
        int: The seed value used.
    """
    if seed is None:
        seed = DEFAULT_SEED

    # Set seed for Python random
    random.seed(seed)
    logger.info(f"Set Python random seed to {seed}")

    # Set seed for NumPy
    try:
        import numpy as np
        np.random.seed(seed)
        logger.info(f"Set NumPy random seed to {seed}")
    except ImportError:
        logger.warning("NumPy not available; skipping NumPy seed initialization")

    # Set seed for PyTorch if available
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
        logger.info(f"Set PyTorch random seed to {seed}")
    except ImportError:
        pass  # PyTorch not required for this pipeline

    return seed


def get_config() -> Dict[str, Any]:
    """
    Retrieve the full configuration dictionary.

    Combines environment variables, default seeds, project paths, and
    hardware constraints (CPU threads, memory limits) from the environment.

    Returns:
        Dict[str, Any]: Complete configuration dictionary.
    """
    # Load environment variables
    env_config = load_env_vars()

    # Initialize random seed
    seed = set_random_seed()

    # Define project paths based on the established structure
    # Assumes this file is at <project_root>/code/config.py
    project_root = Path(__file__).resolve().parent.parent
    data_dir = project_root / "data"
    code_dir = project_root / "code"
    results_dir = project_root / "results"
    tests_dir = project_root / "tests"

    # Ensure specific subdirectories exist for the pipeline
    processed_data_dir = data_dir / "processed"
    raw_data_dir = data_dir / "raw"
    figures_dir = results_dir / "plots"

    for directory in [data_dir, code_dir, results_dir, tests_dir,
                      processed_data_dir, raw_data_dir, figures_dir]:
        directory.mkdir(parents=True, exist_ok=True)

    # Read CPU thread limit and memory limit from environment variables
    # with fallback to defaults defined in constants
    cpu_threads = int(os.getenv("CPU_THREADS", str(DEFAULT_CPU_THREADS)))
    memory_limit_gb = float(os.getenv("MEMORY_LIMIT_GB", str(DEFAULT_MEMORY_LIMIT_GB)))

    config = {
        "seed": seed,
        "paths": {
            "project_root": str(project_root),
            "data": str(data_dir),
            "code": str(code_dir),
            "results": str(results_dir),
            "tests": str(tests_dir),
            "raw_data": str(raw_data_dir),
            "processed_data": str(processed_data_dir),
            "figures": str(figures_dir),
        },
        "api_keys": env_config,
        "cpu_threads": cpu_threads,
        "memory_limit_gb": memory_limit_gb,
    }

    logger.info(f"Configuration loaded. Seed: {seed}, CPU threads: {cpu_threads}, "
                f"Memory limit: {memory_limit_gb} GB")
    return config


# Initialize configuration on module load for convenience
CONFIG = get_config()