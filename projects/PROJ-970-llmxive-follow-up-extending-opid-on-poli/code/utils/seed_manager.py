"""
Seed Manager Module for llmXive Reproducibility

This module centralizes all random seed initialization logic to ensure
reproducibility across runs for numpy, python random, and any other
relevant libraries used in the project.
"""
import random
import os
import sys
import numpy as np
from typing import Optional, Dict, Any

# Import existing config functions to ensure consistency
# These are defined in code/config.py
try:
    from config import set_seed as config_set_seed, get_seed as config_get_seed, get_version_hash
except ImportError:
    # Fallback for standalone execution during testing if config isn't in path
    # In the actual project, config.py is in the root code/ directory
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from config import set_seed as config_set_seed, get_seed as config_get_seed, get_version_hash


def initialize_reproducibility(seed: Optional[int] = None) -> int:
    """
    Initialize all random number generators with the specified seed.
    
    This function ensures that:
    1. Python's built-in random module is seeded
    2. NumPy's random number generator is seeded
    3. The project's central seed configuration is updated
    
    Args:
        seed (Optional[int]): The seed value to use. If None, retrieves 
                              the seed from the project configuration.
                              
    Returns:
        int: The seed value that was used for initialization.
            
    Raises:
        ValueError: If the seed is negative or if configuration retrieval fails.
    """
    if seed is None:
        seed = config_get_seed()
        
    if seed is None:
        raise ValueError("No seed provided and no default seed found in configuration. "
                       "Please set a seed in config.py or pass one to this function.")
    
    if not isinstance(seed, int) or seed < 0:
        raise ValueError(f"Seed must be a non-negative integer, got: {seed}")
    
    # Set seed for Python's random module
    random.seed(seed)
    
    # Set seed for NumPy
    np.random.seed(seed)
    
    # Update the project's central seed configuration
    config_set_seed(seed)
    
    # Log the initialization (using standard logging to avoid circular imports)
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Reproducibility initialized with seed: {seed}")
    
    return seed


def get_current_seed() -> int:
    """
    Retrieve the currently active seed from the project configuration.
    
    Returns:
        int: The current seed value.
        
    Raises:
        ValueError: If no seed is configured.
    """
    seed = config_get_seed()
    if seed is None:
        raise ValueError("No seed is currently configured. "
                       "Call initialize_reproducibility() first.")
    return seed


def get_version_info() -> Dict[str, Any]:
    """
    Get version and reproducibility information for logging and tracking.
    
    Returns:
        Dict containing seed, version hash, and environment info.
    """
    try:
        version_hash = get_version_hash()
    except Exception:
        version_hash = "unknown"
        
    return {
        "seed": get_current_seed(),
        "version_hash": version_hash,
        "python_version": sys.version,
        "numpy_version": np.__version__
    }


def main():
    """
    CLI entry point for testing seed initialization.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Test seed initialization")
    parser.add_argument("--seed", type=int, default=None, help="Seed value to use")
    args = parser.parse_args()
    
    try:
        seed = initialize_reproducibility(args.seed)
        print(f"Successfully initialized reproducibility with seed: {seed}")
        
        # Verify initialization by generating some random numbers
        print("Verification samples:")
        print(f"  random.random(): {random.random():.6f}")
        print(f"  np.random.rand(): {np.random.rand():.6f}")
        
        version_info = get_version_info()
        print(f"Version info: {version_info}")
        
    except Exception as e:
        print(f"Error initializing reproducibility: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()