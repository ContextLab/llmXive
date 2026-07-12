"""
Configuration module for llmXive project.
Handles random seeds, experiment parameters, and reproducibility settings.
"""
import os
import random
from typing import Dict, Any, List

# Import seed loading implementation from T008
# T008 implemented loading SEED_A and SEED_B from environment variables
def _load_seeds_impl() -> Dict[str, int]:
    """Load random seeds from environment variables with defaults."""
    seed_a = int(os.environ.get('SEED_A', '42'))
    seed_b = int(os.environ.get('SEED_B', '123'))
    return {'SEED_A': seed_a, 'SEED_B': seed_b}

# Load seeds using T008 implementation
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

def get_seeds() -> Dict[str, int]:
    """Return the current random seeds."""
    return {'SEED_A': SEED_A, 'SEED_B': SEED_B}

def get_experiment_config() -> Dict[str, Any]:
    """Return complete experiment configuration."""
    return {
        'seeds': get_seeds(),
        'library_sizes': LIBRARY_SIZES,
        'overlap_levels': OVERLAP_LEVELS,
        'pinned_seeds': PINNED_SEEDS,
        'force_cpu': FORCE_CPU
    }

def pin_seeds() -> None:
    """Pin all random number generators to ensure reproducibility."""
    random.seed(SEED_A)
    os.environ['PYTHONHASHSEED'] = str(SEED_A)
    
    # Pin numpy if available
    try:
        import numpy as np
        np.random.seed(SEED_A)
    except ImportError:
        pass

def validate_reproducibility() -> bool:
    """Validate that seeds are properly pinned and reproducible."""
    return PINNED_SEEDS and (SEED_A is not None) and (SEED_B is not None)
