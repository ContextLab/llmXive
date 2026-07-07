import os
import random
import logging
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# Default configuration values
DEFAULT_CONFIG = {
    "random_seed": 42,
    "cpu_threads": 1,
    "memory_limit_gb": 8.0,
    "nasa_api_key": "",
    "retrieval_timeout": 300,
    "retry_attempts": 3,
}

def load_env_vars() -> Dict[str, str]:
    """
    Load environment variables for API keys and sensitive configuration.
    
    Reads from os.environ. If a variable is not set, it returns an empty string.
    This function ensures that API keys (e.g., NASA Exoplanet Archive) are
    available to the application without hardcoding them.
    
    Returns:
        Dict[str, str]: A dictionary of environment variables.
    """
    env_vars = {
        "NASA_API_KEY": os.environ.get("NASA_API_KEY", ""),
        "RANDOM_SEED": os.environ.get("RANDOM_SEED", ""),
        "CPU_THREADS": os.environ.get("CPU_THREADS", ""),
        "MEMORY_LIMIT_GB": os.environ.get("MEMORY_LIMIT_GB", ""),
    }
    
    # Log which keys are present (without exposing values)
    for key, value in env_vars.items():
        if value:
            logger.debug(f"Environment variable {key} is set.")
        else:
            logger.debug(f"Environment variable {key} is NOT set.")
    
    return env_vars

def set_random_seed(seed: Optional[int] = None) -> int:
    """
    Set the random seed for reproducibility across the pipeline.
    
    Priority of seed selection:
    1. Explicit argument passed to function
    2. Environment variable RANDOM_SEED
    3. Default value (42)
    
    Args:
        seed (Optional[int]): The seed value to use.
        
    Returns:
        int: The seed value that was set.
    """
    if seed is not None:
        final_seed = seed
    else:
        env_seed = os.environ.get("RANDOM_SEED")
        if env_seed:
            try:
                final_seed = int(env_seed)
                logger.info(f"Using random seed from environment: {final_seed}")
            except ValueError:
                logger.warning(f"Invalid RANDOM_SEED in environment: {env_seed}. Using default.")
                final_seed = DEFAULT_CONFIG["random_seed"]
        else:
            final_seed = DEFAULT_CONFIG["random_seed"]
            logger.info(f"Using default random seed: {final_seed}")
    
    # Set seeds for Python's random, NumPy, and ensure reproducibility
    random.seed(final_seed)
    try:
        import numpy as np
        np.random.seed(final_seed)
    except ImportError:
        pass # NumPy might not be installed yet or needed for this specific step
    
    return final_seed

def get_config() -> Dict[str, Any]:
    """
    Retrieve the full configuration dictionary for the pipeline.
    
    This function aggregates configuration from:
    1. Environment variables (API keys, seeds, resource limits)
    2. Default configuration values
    
    It also validates and casts types where necessary.
    
    Returns:
        Dict[str, Any]: The complete configuration dictionary.
    """
    env_vars = load_env_vars()
    
    config = DEFAULT_CONFIG.copy()
    
    # Override with environment variables if present
    if env_vars["NASA_API_KEY"]:
        config["nasa_api_key"] = env_vars["NASA_API_KEY"]
    
    if env_vars["CPU_THREADS"]:
        try:
            config["cpu_threads"] = int(env_vars["CPU_THREADS"])
        except ValueError:
            logger.warning(f"Invalid CPU_THREADS in environment: {env_vars['CPU_THREADS']}. Using default.")
    
    if env_vars["MEMORY_LIMIT_GB"]:
        try:
            config["memory_limit_gb"] = float(env_vars["MEMORY_LIMIT_GB"])
        except ValueError:
            logger.warning(f"Invalid MEMORY_LIMIT_GB in environment: {env_vars['MEMORY_LIMIT_GB']}. Using default.")
    
    # Random seed is handled separately via set_random_seed, but we include it in config
    # The seed is set as a side effect of calling this if needed, or explicitly by the caller.
    # For consistency, we ensure the seed is set here if not already set by the caller.
    # However, to avoid side effects on import, we rely on the caller to call set_random_seed().
    # We just include the value in the config dict based on env or default.
    seed_val = os.environ.get("RANDOM_SEED")
    if seed_val:
        try:
            config["random_seed"] = int(seed_val)
        except ValueError:
            config["random_seed"] = DEFAULT_CONFIG["random_seed"]
    
    return config