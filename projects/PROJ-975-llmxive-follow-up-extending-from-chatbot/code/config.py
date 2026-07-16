"""
Configuration module for llmXive project.
Handles random seeds, experiment parameters, and reproducibility settings.

T008 Implementation: Loads SEED_A and SEED_B from environment variables
with deterministic defaults to ensure reproducibility in fresh CI runs.
"""
import os
import random
from typing import Dict, Any, List

# T008: Load seeds from environment variables with deterministic defaults
# Defaults defined in T005 (SEED_A=42, SEED_B=123)
def _load_seeds_impl() -> Dict[str, int]:
    """
    Load random seeds from environment variables.
    
    Returns:
        Dict with SEED_A and SEED_B as integers.
        
    Behavior:
        - Reads SEED_A from os.environ, defaults to 42 if missing.
        - Reads SEED_B from os.environ, defaults to 123 if missing.
        - Ensures values are integers for reproducibility.
    """
    seed_a_str = os.environ.get('SEED_A', '42')
    seed_b_str = os.environ.get('SEED_B', '123')
    
    try:
        seed_a = int(seed_a_str)
        seed_b = int(seed_b_str)
    except ValueError as e:
        raise ValueError(
            f"Environment variables SEED_A and SEED_B must be integers. "
            f"Got SEED_A='{seed_a_str}', SEED_B='{seed_b_str}'"
        ) from e
        
    return {'SEED_A': seed_a, 'SEED_B': seed_b}

# Load seeds using T008 implementation at module import time
_seeds = _load_seeds_impl()
SEED_A = _seeds['SEED_A']
SEED_B = _seeds['SEED_B']

# Experiment parameters (T005)
LIBRARY_SIZES: List[int] = [10, 30, 50, 100]
OVERLAP_LEVELS: Dict[str, float] = {
    'low': 0.25,
    'medium': 0.55,
    'high': 0.85
}

# Reproducibility settings
PINNED_SEEDS = True
FORCE_CPU = True

# T005: Define the complete EXPERIMENT_CONFIG dictionary as required
EXPERIMENT_CONFIG: Dict[str, Any] = {
    'SEED_A': SEED_A,
    'SEED_B': SEED_B,
    'LIBRARY_SIZES': LIBRARY_SIZES,
    'OVERLAP_LEVELS': OVERLAP_LEVELS
}

def get_seeds() -> Dict[str, int]:
    """
    Return the current random seeds.
    
    Returns:
        Dict containing SEED_A and SEED_B.
    """
    return {'SEED_A': SEED_A, 'SEED_B': SEED_B}

def get_experiment_config() -> Dict[str, Any]:
    """
    Return complete experiment configuration.
    
    Returns:
        Dict containing seeds, library sizes, overlap levels, and flags.
    """
    return {
        'seeds': get_seeds(),
        'library_sizes': LIBRARY_SIZES,
        'overlap_levels': OVERLAP_LEVELS,
        'pinned_seeds': PINNED_SEEDS,
        'force_cpu': FORCE_CPU
    }

def pin_seeds() -> None:
    """
    Pin all random number generators to ensure reproducibility.
    
    Sets seeds for:
        - Python's random module
        - PYTHONHASHSEED environment variable
        - numpy (if available)
    """
    random.seed(SEED_A)
    os.environ['PYTHONHASHSEED'] = str(SEED_A)
    
    # Pin numpy if available
    try:
        import numpy as np
        np.random.seed(SEED_A)
    except ImportError:
        pass

def validate_reproducibility() -> bool:
    """
    Validate that seeds are properly pinned and reproducible.
    
    Returns:
        True if PINNED_SEEDS is True and both SEED_A and SEED_B are set.
    """
    return PINNED_SEEDS and (SEED_A is not None) and (SEED_B is not None)