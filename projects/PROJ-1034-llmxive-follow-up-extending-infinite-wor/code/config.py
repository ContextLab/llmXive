"""
Central configuration for deterministic random seeds and reproducibility.

This module ensures that all random number generators (numpy, random, torch)
are seeded consistently across runs to guarantee reproducibility of simulation results.
"""
import os
import random
import hashlib
from typing import Optional, Dict, Any

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False


# Default seed if none is provided via environment or arguments
DEFAULT_SEED = 42
SEED_ENV_VAR = "LLMXIVE_SEED"


def get_seed_from_env(default: int = DEFAULT_SEED) -> int:
    """
    Retrieve the seed from the environment variable LLMXIVE_SEED.
    If not set, returns the provided default.
    """
    seed_str = os.environ.get(SEED_ENV_VAR)
    if seed_str is not None:
        try:
            return int(seed_str)
        except ValueError:
            # If the env var is not a valid integer, log a warning and fallback
            # In a real logging setup, we would print a warning here.
            return default
    return default


def set_seed(seed: int) -> Dict[str, bool]:
    """
    Set the random seed for all supported libraries to ensure reproducibility.
    
    Args:
        seed: The integer seed value.
        
    Returns:
        A dictionary indicating which libraries were successfully seeded.
    """
    status = {
        "random": False,
        "numpy": False,
        "torch": False,
        "os_env": False
    }

    # Seed Python's built-in random module
    random.seed(seed)
    status["random"] = True

    # Seed numpy
    if HAS_NUMPY:
        np.random.seed(seed)
        status["numpy"] = True

    # Seed PyTorch (if available)
    if HAS_TORCH:
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed(seed)
            torch.cuda.manual_seed_all(seed)
            # Ensure deterministic behavior in CUDA operations
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False
        status["torch"] = True

    # Set environment variable for external processes (optional but good practice)
    os.environ[SEED_ENV_VAR] = str(seed)
    status["os_env"] = True

    return status


def initialize_reproducibility(seed: Optional[int] = None) -> Dict[str, Any]:
    """
    Main entry point for initializing reproducibility in the simulation pipeline.
    
    This function checks for a seed in the environment, uses a provided seed,
    or falls back to the default. It then seeds all relevant libraries.
    
    Args:
        seed: Optional explicit seed. If None, checks environment or uses default.
        
    Returns:
        A dictionary containing the effective seed and the seeding status.
    """
    effective_seed = seed if seed is not None else get_seed_from_env()
    seeding_status = set_seed(effective_seed)
    
    return {
        "seed": effective_seed,
        "status": seeding_status,
        "message": f"Reproducibility initialized with seed={effective_seed}"
    }


def get_config_hash(config: Dict[str, Any]) -> str:
    """
    Generate a deterministic hash of a configuration dictionary.
    Useful for creating unique output filenames based on configuration.
    
    Args:
        config: The configuration dictionary to hash.
        
    Returns:
        A hexadecimal string representing the hash of the sorted config.
    """
    # Convert to a sorted string to ensure deterministic ordering
    config_str = str(sorted(config.items()))
    return hashlib.sha256(config_str.encode('utf-8')).hexdigest()[:16]
