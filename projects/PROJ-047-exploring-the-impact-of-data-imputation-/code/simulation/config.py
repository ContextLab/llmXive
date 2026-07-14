"""
Configuration and hyperparameters for the simulation pipeline.

This module defines the fixed parameters for the study:
- Beta sweep values for the MNAR mechanism strength.
- Sample size (N) per dataset.
- Number of replications per beta value.
- Random seed management utilities.
"""

from typing import List, Tuple
import numpy as np
import hashlib
import os

# =============================================================================
# Hyperparameters
# =============================================================================

# Beta values to sweep: Represents the strength of the MNAR mechanism
# (correlation between missingness and the outcome Y).
BETA_SWEEP: List[float] = [0.0, 0.2, 0.5, 0.8, 1.0]

# Sample size per dataset (N)
SAMPLE_SIZE: int = 1000

# Number of replications (simulations) to run for each beta value
REPLICATIONS_PER_BETA: int = 200

# Base seed for the entire experiment to ensure reproducibility across the sweep
BASE_SEED: int = 42

# =============================================================================
# Random Seed Management
# =============================================================================

def get_run_seed(base_seed: int, beta: float, replication_index: int) -> int:
    """
    Generates a deterministic, unique seed for a specific run based on
    the beta value and replication index.

    This ensures that for a given (beta, replication_index), the same
    random state is always produced, satisfying the Constitution Principle VI.

    Args:
        base_seed: The global base seed for the experiment.
        beta: The current beta value being tested.
        replication_index: The index of the current replication (0 to REPLICATIONS_PER_BETA - 1).

    Returns:
        An integer seed suitable for numpy.random.Generator or random.seed().
    """
    # Create a deterministic string representation
    seed_string = f"{base_seed}_{beta}_{replication_index}"
    
    # Hash the string to generate a large integer seed
    hash_obj = hashlib.sha256(seed_string.encode('utf-8'))
    hash_hex = hash_obj.hexdigest()
    
    # Convert first 16 hex chars to an integer (fits in 64-bit integer)
    return int(hash_hex[:16], 16)

def get_experiment_rng(base_seed: int = BASE_SEED) -> np.random.Generator:
    """
    Creates a root random number generator for the experiment.
    
    Args:
        base_seed: The base seed to initialize the generator.
        
    Returns:
        A numpy.random.Generator instance.
    """
    return np.random.default_rng(base_seed)

# =============================================================================
# Simulation Loop Configuration
# =============================================================================

def get_simulation_grid() -> List[Tuple[float, int]]:
    """
    Generates the list of (beta, replication_index) pairs to iterate over.
    
    Returns:
        A list of tuples where each tuple is (beta_value, replication_index).
    """
    grid = []
    for beta in BETA_SWEEP:
        for i in range(REPLICATIONS_PER_BETA):
            grid.append((beta, i))
    return grid