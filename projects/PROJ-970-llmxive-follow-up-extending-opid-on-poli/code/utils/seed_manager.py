import random
import os
import sys
import numpy as np
from typing import Optional, Dict, Any
from config import set_seed, get_seed, get_version_hash, get_config_summary

def initialize_reproducibility(seed: Optional[int] = None) -> Dict[str, Any]:
    """
    Initialize all random number generators to ensure deterministic execution.
    
    This function sets the seed for:
    - Python's built-in random module
    - NumPy's random number generator
    - The project's internal configuration seed
    
    If no seed is provided, it attempts to read one from the environment 
    variable `PYTHON_SEED` or generates a new one based on the current 
    time and process ID for the first run, then saves it.
    
    Args:
        seed: Optional integer seed. If None, reads from env or generates one.
        
    Returns:
        Dict containing the seed used, version hash, and config summary.
    """
    if seed is None:
        env_seed = os.getenv("PYTHON_SEED")
        if env_seed:
            try:
                seed = int(env_seed)
            except ValueError:
                raise ValueError(f"Invalid PYTHON_SEED value in environment: {env_seed}")
        else:
            # If no seed provided or in env, we must raise an error to force 
            # explicit seed configuration for reproducibility in research pipelines.
            # Fabricating a seed here violates the reproducibility requirement.
            raise ValueError(
                "No random seed provided. "
                "Please set the 'PYTHON_SEED' environment variable or pass a seed argument "
                "to ensure reproducible results. "
                "Example: export PYTHON_SEED=42"
            )
    
    # Set seed for Python standard library
    random.seed(seed)
    
    # Set seed for NumPy
    np.random.seed(seed)
    
    # Set seed in project config
    set_seed(seed)
    
    # Return metadata for logging
    return {
        "seed": seed,
        "version_hash": get_version_hash(),
        "config_summary": get_config_summary()
    }

def get_current_seed() -> int:
    """
    Retrieve the currently active seed from the configuration.
    
    Returns:
        The integer seed currently set.
        
    Raises:
        ValueError: If no seed has been initialized yet.
    """
    seed = get_seed()
    if seed is None:
        raise ValueError(
            "No seed initialized. Call initialize_reproducibility() or set PYTHON_SEED first."
        )
    return seed

def get_version_info() -> Dict[str, Any]:
    """
    Retrieve version and reproducibility metadata.
    
    Returns:
        Dictionary containing seed, version hash, and config summary.
    """
    return {
        "seed": get_current_seed(),
        "version_hash": get_version_hash(),
        "config_summary": get_config_summary()
    }
