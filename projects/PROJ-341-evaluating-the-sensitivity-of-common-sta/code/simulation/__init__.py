"""
Simulation module initialization with logging integration.
"""
import logging
from .logging_config import setup_logging, get_logger, log_simulation_params
from .data_generator import generate_normal_data, generate_multinomial_data, generate_contingency_table_data, validate_distribution_params
from .test_runner import run_t_test, run_anova, run_chi_squared, run_simulation_condition, aggregate_results
from .chi_squared_utils import calculate_expected_counts, check_low_expected_counts, run_chi_squared_with_fallback
from .output_writer import write_p_values_raw, load_p_values_raw

# Initialize logger for the simulation module
_logger = setup_logging()

def get_rng(seed: int):
    """
    Create a deterministic random number generator.
    
    Args:
        seed: Random seed for reproducibility
    
    Returns:
        numpy.random.Generator instance
    """
    import numpy as np
    log_seed_usage(seed, "rng", _logger)
    return np.random.default_rng(seed)

def log_seed_usage(seed: int, module: str) -> None:
    """
    Log the usage of a random seed for reproducibility tracking.
    
    Args:
        seed: The random seed value
        module: The module where the seed was used
    """
    from .logging_config import log_seed_usage as _log_seed
    _log_seed(seed, module, _logger)

__all__ = [
    'setup_logging',
    'get_logger',
    'log_simulation_params',
    'get_rng',
    'generate_normal_data',
    'generate_multinomial_data',
    'generate_contingency_table_data',
    'validate_distribution_params',
    'run_t_test',
    'run_anova',
    'run_chi_squared',
    'run_simulation_condition',
    'aggregate_results',
    'calculate_expected_counts',
    'check_low_expected_counts',
    'run_chi_squared_with_fallback',
    'write_p_values_raw',
    'load_p_values_raw'
]
