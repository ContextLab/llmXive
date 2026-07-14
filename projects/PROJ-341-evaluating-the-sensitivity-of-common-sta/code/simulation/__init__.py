"""
Simulation module for generating synthetic data and running statistical tests.
Provides deterministic random number generation and core simulation utilities.
"""
import numpy as np
from typing import Optional
import json
import os

# Global RNG state for reproducibility
_global_seed: Optional[int] = None
_rng: Optional[np.random.Generator] = None

def set_seed(seed: int):
    """
    Set the global random seed for reproducibility.
    
    Args:
        seed: Integer seed value
    """
    global _global_seed, _rng
    _global_seed = seed
    _rng = np.random.default_rng(seed)

def get_seed() -> Optional[int]:
    """
    Get the currently set global seed.
    
    Returns:
        The seed value or None if not set.
    """
    return _global_seed

def get_rng(seed: Optional[int] = None) -> np.random.Generator:
    """
    Get a random number generator.
    
    If a seed is provided, it creates a new RNG with that seed.
    If no seed is provided, uses the global RNG if set, otherwise creates a new one.
    
    Args:
        seed: Optional specific seed for this RNG
    
    Returns:
        np.random.Generator instance
    """
    if seed is not None:
        return np.random.default_rng(seed)
    
    if _rng is not None:
        return _rng
    
    # Fallback: create a new RNG with a default seed if none set
    return np.random.default_rng(42)

def reset_rng():
    """Reset the global RNG to its initial state."""
    global _rng
    if _global_seed is not None:
        _rng = np.random.default_rng(_global_seed)
    else:
        _rng = None

# Import submodules to expose their public APIs
from code.simulation.data_generator import (
    generate_normal_data,
    generate_multinomial_data,
    generate_contingency_table_data,
    validate_distribution_params
)
from code.simulation.test_runner import (
    run_t_test,
    run_anova,
    run_chi_squared,
    run_simulation_condition,
    aggregate_results
)
from code.simulation.chi_squared_utils import (
    calculate_expected_counts,
    check_low_expected_counts,
    run_chi_squared_with_fallback
)
from code.simulation.output_writer import (
    write_p_values_raw,
    load_p_values_raw
)

__all__ = [
    # RNG functions
    'set_seed', 'get_seed', 'get_rng', 'reset_rng',
    # Data generation
    'generate_normal_data',
    'generate_multinomial_data',
    'generate_contingency_table_data',
    'validate_distribution_params',
    # Test running
    'run_t_test',
    'run_anova',
    'run_chi_squared',
    'run_simulation_condition',
    'aggregate_results',
    # Chi-squared utilities
    'calculate_expected_counts',
    'check_low_expected_counts',
    'run_chi_squared_with_fallback',
    # Output writing
    'write_p_values_raw',
    'load_p_values_raw'
]