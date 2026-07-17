"""
Configuration management for llmXive pipeline.
Handles environment variables, random seeds, and resource limits.
"""
import os
import random
from typing import Optional

# Resource Limits as defined in T005
# These can be overridden by environment variables
MAX_CPU_CORES = int(os.environ.get("MAX_CPU_CORES", 2))
MAX_MEMORY_GB = float(os.environ.get("MAX_MEMORY_GB", 7))

def set_seed(seed: int = 42):
    """
    Sets random seeds for reproducibility.
    
    Args:
        seed: Integer seed value.
    """
    random.seed(seed)
    # If numpy/torch are imported later, they should also be seeded
    # but we avoid importing them here to keep this module lightweight.
    os.environ["PYTHONHASHSEED"] = str(seed)

def validate_resource_limits():
    """
    Validates that the configured resource limits are reasonable.
    
    Returns:
        bool: True if limits are valid, False otherwise.
    """
    if MAX_CPU_CORES < 1:
        raise ValueError("MAX_CPU_CORES must be at least 1.")
    if MAX_MEMORY_GB < 1.0:
        raise ValueError("MAX_MEMORY_GB must be at least 1.0.")
    return True

if __name__ == "__main__":
    print(f"Config loaded: MAX_CPU_CORES={MAX_CPU_CORES}, MAX_MEMORY_GB={MAX_MEMORY_GB}")
    validate_resource_limits()
    set_seed()
    print("Seed set and limits validated.")
