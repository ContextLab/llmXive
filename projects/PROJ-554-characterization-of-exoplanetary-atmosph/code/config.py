"""
Configuration management module for the exoplanetary atmosphere characterization pipeline.

Handles environment variable loading, API key retrieval, and random seed initialization.
"""
import os
import random
import logging
from pathlib import Path
from typing import Optional, Dict, Any
import numpy as np
from dotenv import load_dotenv

# Initialize logger
logger = logging.getLogger(__name__)

def load_env_vars(env_path: Optional[str] = None) -> bool:
    """
    Load environment variables from a .env file if it exists.
    
    Args:
        env_path: Path to the .env file. If None, looks for .env in project root.
        
    Returns:
        True if file was loaded and processed, False if file not found or error.
    """
    if env_path is None:
        # Default to project root
        env_path = str(Path(__file__).parent.parent / ".env")
    
    if os.path.exists(env_path):
        loaded = load_dotenv(env_path)
        if loaded:
            logger.info(f"Loaded environment variables from {env_path}")
            return True
        else:
            logger.warning(f"Could not load environment variables from {env_path}")
            return False
    else:
        logger.info(f"No .env file found at {env_path}, skipping load")
        return False

def set_random_seed(seed: Optional[int] = None) -> int:
    """
    Set random seeds for reproducibility across all relevant libraries.
    
    Args:
        seed: The seed value. If None, reads from 'RANDOM_SEED' environment variable.
              If env var is not set, uses a default value of 42.
              
    Returns:
        The seed value that was set.
    """
    if seed is None:
        seed_str = os.getenv("RANDOM_SEED")
        if seed_str is not None:
            try:
                seed = int(seed_str)
                logger.info(f"Using seed {seed} from RANDOM_SEED environment variable")
            except ValueError:
                logger.warning(f"Invalid RANDOM_SEED value '{seed_str}', using default 42")
                seed = 42
        else:
            seed = 42
            logger.info("No RANDOM_SEED set, using default value 42")
    
    # Set seeds for reproducibility
    random.seed(seed)
    np.random.seed(seed)
    
    # Note: If using tensorflow or torch, add their seed settings here
    # os.environ['PYTHONHASHSEED'] = str(seed)
    
    logger.debug(f"Random seeds set to {seed}")
    return seed

def get_config() -> Dict[str, Any]:
    """
    Retrieve the current configuration state.
    
    Returns:
        Dictionary containing configuration values including paths, seeds, and API keys.
    """
    # Ensure environment variables are loaded
    load_env_vars()
    
    config = {
        "random_seed": os.getenv("RANDOM_SEED", "42"),
        "api_keys": {
            "nasa_exoplanet_archive": os.getenv("NASA_EXOPLANET_ARCHIVE_KEY"),
            "hubble_archive": os.getenv("HUBBLE_ARCHIVE_KEY"),
            "jwst_archive": os.getenv("JWST_ARCHIVE_KEY")
        },
        "paths": {
            "project_root": str(Path(__file__).parent.parent),
            "data_raw": str(Path(__file__).parent.parent / "data" / "raw"),
            "data_processed": str(Path(__file__).parent.parent / "data" / "processed"),
            "results": str(Path(__file__).parent.parent / "results"),
            "figures": str(Path(__file__).parent.parent / "results" / "plots")
        },
        "cpu_threads": int(os.getenv("CPU_THREADS", "4")),
        "memory_limit_gb": float(os.getenv("MEMORY_LIMIT_GB", "8.0"))
    }
    
    # Log sensitive info safely (mask keys)
    masked_keys = {k: "****" if v else "None" for k, v in config["api_keys"].items()}
    config["masked_api_keys"] = masked_keys
    
    logger.debug(f"Configuration loaded: {config}")
    return config

def validate_config(config: Optional[Dict[str, Any]] = None) -> bool:
    """
    Validate that required configuration values are present and valid.
    
    Args:
        config: Configuration dictionary. If None, loads from get_config().
                
    Returns:
        True if configuration is valid, False otherwise.
    """
    if config is None:
        config = get_config()
    
    errors = []
    
    # Check paths exist
    for key, path_str in config["paths"].items():
        if key != "project_root":  # project_root is guaranteed to exist
            path = Path(path_str)
            if not path.exists():
                errors.append(f"Path does not exist: {path}")
    
    # Check random seed is valid integer
    try:
        int(config["random_seed"])
    except ValueError:
        errors.append(f"Invalid random_seed value: {config['random_seed']}")
    
    # Check CPU threads is positive
    if config["cpu_threads"] <= 0:
        errors.append(f"CPU threads must be positive: {config['cpu_threads']}")
    
    # Check memory limit is positive
    if config["memory_limit_gb"] <= 0:
        errors.append(f"Memory limit must be positive: {config['memory_limit_gb']}")
    
    if errors:
        for error in errors:
            logger.error(f"Configuration error: {error}")
        return False
    
    logger.info("Configuration validation passed")
    return True

def main():
    """
    Main function to demonstrate configuration loading and validation.
    """
    print("Loading configuration...")
    load_env_vars()
    
    config = get_config()
    print(f"Random Seed: {config['random_seed']}")
    print(f"CPU Threads: {config['cpu_threads']}")
    print(f"Memory Limit: {config['memory_limit_gb']} GB")
    print(f"API Keys Status: {config['masked_api_keys']}")
    print(f"Paths: {config['paths']}")
    
    if validate_config(config):
        print("Configuration is valid.")
    else:
        print("Configuration validation failed.")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
