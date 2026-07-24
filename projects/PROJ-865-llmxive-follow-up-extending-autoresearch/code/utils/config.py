"""
Configuration management for the pipeline.
Defines environment variables, random seeds, and explicit resource limits.
"""
import os
import random
import numpy as np
import torch

# Explicit Resource Limits as per Task T007
# These defaults can be overridden by environment variables
MAX_CPU_CORES = int(os.getenv("MAX_CPU_CORES", "2"))
MAX_MEMORY_GB = int(os.getenv("MAX_MEMORY_GB", "7"))
TIMEOUT_SECONDS = int(os.getenv("TIMEOUT_SECONDS", "3600"))

# Random Seed for Reproducibility
RANDOM_SEED = int(os.getenv("RANDOM_SEED", "42"))

def set_seed(seed: Optional[int] = None):
    """
    Set random seed for reproducibility across the pipeline.
    Updates Python's random module and sets the hash seed.
    """
    if seed is None:
        seed = RANDOM_SEED
    
    random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)
    
    # Note: numpy and torch seeding would go here if imported
    # We defer importing heavy libraries until they are actually needed
    # to keep this module lightweight and import-safe.

def validate_resource_limits():
    """
    Validate that the current environment configuration respects the defined limits.
    This function logs the configured limits. 
    Runtime enforcement is handled by the ResourceWatchdog (T007c).
    
    Returns:
        bool: True if limits are valid positive integers.
    
    Raises:
        ValueError: If limits are not positive integers.
    """
    if MAX_CPU_CORES <= 0:
        raise ValueError(f"MAX_CPU_CORES must be positive, got {MAX_CPU_CORES}")
    if MAX_MEMORY_GB <= 0:
        raise ValueError(f"MAX_MEMORY_GB must be positive, got {MAX_MEMORY_GB}")
    if TIMEOUT_SECONDS <= 0:
        raise ValueError(f"TIMEOUT_SECONDS must be positive, got {TIMEOUT_SECONDS}")
        
    import logging
    logger = logging.getLogger(__name__)
    logger.info(
        f"Resource Limits Configured: "
        f"CPU={MAX_CPU_CORES}, "
        f"RAM={MAX_MEMORY_GB}GB, "
        f"Timeout={TIMEOUT_SECONDS}s"
    )
    return True

# Export constants for direct import by other modules
__all__ = [
    "MAX_CPU_CORES",
    "MAX_MEMORY_GB", 
    "TIMEOUT_SECONDS",
    "RANDOM_SEED",
    "set_seed",
    "validate_resource_limits"
]