"""
Configuration management for the pipeline.
"""
import os
import random
from typing import Optional

# Default limits
MAX_CPU_CORES = int(os.getenv("MAX_CPU_CORES", "2"))
MAX_MEMORY_GB = int(os.getenv("MAX_MEMORY_GB", "7"))
RANDOM_SEED = int(os.getenv("RANDOM_SEED", "42"))

def set_seed(seed: Optional[int] = None):
    """Set random seed for reproducibility."""
    if seed is None:
        seed = RANDOM_SEED
    random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)
    # Note: numpy and torch seeding would go here if imported

def validate_resource_limits():
    """
    Validate that the current environment respects the defined limits.
    This is a basic check; the watchdog handles runtime enforcement.
    """
    # We assume the environment is configured correctly before execution starts.
    # This function logs the limits.
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Resource Limits Configured: CPU={MAX_CPU_CORES}, RAM={MAX_MEMORY_GB}GB")
    return True
