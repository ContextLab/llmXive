import os
import random
from typing import Dict, Any, List

# Default seeds
DEFAULT_SEED_A = 42
DEFAULT_SEED_B = 123

def get_seeds() -> Dict[str, int]:
    """
    Returns a dictionary of seeds, prioritizing environment variables.
    """
    seed_a = int(os.getenv('SEED_A', DEFAULT_SEED_A))
    seed_b = int(os.getenv('SEED_B', DEFAULT_SEED_B))
    return {'seed_a': seed_a, 'seed_b': seed_b}

SEED_A = get_seeds()['seed_a']
SEED_B = get_seeds()['seed_b']

def pin_seeds():
    """
    Pins random seeds for reproducibility.
    """
    seeds = get_seeds()
    random.seed(seeds['seed_a'])
    # numpy is handled in utils.py usually, but we can set it here if needed
    try:
        import numpy as np
        np.random.seed(seeds['seed_a'])
    except ImportError:
        pass

def get_experiment_config() -> Dict[str, Any]:
    """
    Loads experiment configuration from environment or defaults.
    """
    config = {
        'pruning_interval': int(os.getenv('PRUNING_INTERVAL', 10)),
        'overlap_level': os.getenv('OVERLAP_LEVEL', 'medium'),
        'library_sizes': [10, 20, 50, 100],
        'k_retrieval': 5,
        'threshold_sim': 0.70
    }
    return config

def validate_reproducibility():
    """
    Validates that seeds are set correctly.
    """
    seeds = get_seeds()
    if seeds['seed_a'] == DEFAULT_SEED_A and seeds['seed_b'] == DEFAULT_SEED_B:
        print(f"Using default seeds: A={seeds['seed_a']}, B={seeds['seed_b']}")
    else:
        print(f"Using environment seeds: A={seeds['seed_a']}, B={seeds['seed_b']}")
