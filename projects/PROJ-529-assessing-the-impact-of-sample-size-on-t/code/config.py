"""Configuration management for the project.

This module provides centralized configuration management for the meta-analysis
impact study. It reads settings from environment variables with sensible defaults
for both real-world data acquisition and simulation modes.
"""

import os
from typing import Optional, Dict, Any

# Global configuration cache to avoid repeated environment reads
_config_cache: Optional[Dict[str, Any]] = None

def get_config() -> Dict[str, Any]:
    """
    Get project configuration from environment variables or defaults.

    This function supports two primary modes of operation:
    - 'real': Acquire data from Cochrane/Campbell APIs
    - 'simulation': Generate synthetic data based on literature parameters

    Environment Variables:
        DATA_SOURCE: 'real' or 'simulation' (default: 'simulation')
        NOMINAL_COVERAGE_TARGET: Target CI coverage rate (default: 0.95)
        STABILITY_THRESHOLD: Minimum change in SD to consider stable (default: 0.05)
        MIN_STUDIES: Minimum number of studies per meta-analysis (default: 3)
        MAX_STUDIES: Maximum number of studies per meta-analysis (default: 50)
        BOOTSTRAP_ITERATIONS: Number of bootstrap subsamples to generate (default: 100)
        BASE_SEED: Base random seed for reproducibility (default: 42)
        REAL_DATA_URL: URL for real data source (optional)

    Returns:
        Dictionary containing configuration values with types:
            - data_source: str
            - nominal_coverage_target: float
            - stability_threshold: float
            - min_studies: int
            - max_studies: int
            - bootstrap_iterations: int
            - base_seed: int
            - real_data_url: str (optional)
    """
    global _config_cache
    
    # Return cached config if available to ensure consistency across calls
    if _config_cache is not None:
        return _config_cache

    config = {
        'data_source': os.getenv('DATA_SOURCE', 'simulation'),
        'nominal_coverage_target': float(os.getenv('NOMINAL_COVERAGE_TARGET', '0.95')),
        'stability_threshold': float(os.getenv('STABILITY_THRESHOLD', '0.05')),
        'min_studies': int(os.getenv('MIN_STUDIES', '3')),
        'max_studies': int(os.getenv('MAX_STUDIES', '50')),
        'bootstrap_iterations': int(os.getenv('BOOTSTRAP_ITERATIONS', '100')),
        'base_seed': int(os.getenv('BASE_SEED', '42')),
    }

    # Optional: Real data source URL
    real_data_url = os.getenv('REAL_DATA_URL')
    if real_data_url:
        config['real_data_url'] = real_data_url

    # Validate data_source value
    if config['data_source'] not in ('real', 'simulation'):
        raise ValueError(
            f"DATA_SOURCE must be 'real' or 'simulation', got: {config['data_source']}"
        )

    # Validate numeric ranges
    if config['min_studies'] < 1:
        raise ValueError(f"MIN_STUDIES must be >= 1, got: {config['min_studies']}")
    
    if config['max_studies'] < config['min_studies']:
        raise ValueError(
            f"MAX_STUDIES ({config['max_studies']}) must be >= MIN_STUDIES ({config['min_studies']})"
        )

    if config['bootstrap_iterations'] < 1:
        raise ValueError(f"BOOTSTRAP_ITERATIONS must be >= 1, got: {config['bootstrap_iterations']}")

    if not (0.0 < config['nominal_coverage_target'] < 1.0):
        raise ValueError(
            f"NOMINAL_COVERAGE_TARGET must be between 0 and 1, got: {config['nominal_coverage_target']}"
        )

    if config['stability_threshold'] <= 0:
        raise ValueError(
            f"STABILITY_THRESHOLD must be > 0, got: {config['stability_threshold']}"
        )

    # Cache the validated config
    _config_cache = config
    return config


def is_real_mode() -> bool:
    """
    Check if the project is configured to use real data sources.

    Returns:
        True if DATA_SOURCE is set to 'real', False otherwise.
    """
    return get_config()['data_source'] == 'real'


def is_simulation_mode() -> bool:
    """
    Check if the project is configured to use simulation mode.

    Returns:
        True if DATA_SOURCE is set to 'simulation', False otherwise.
    """
    return get_config()['data_source'] == 'simulation'

# Constants for direct access as required by FR-007 and SC-003
# These are derived from get_config() to ensure single source of truth
def get_nominal_coverage_target() -> float:
    """
    Get the nominal coverage target (e.g., 0.95 for 95% CI).
    
    Returns:
        float: The target coverage rate.
    """
    return get_config()['nominal_coverage_target']

def get_stability_threshold() -> float:
    """
    Get the stability threshold for determining when effect size stability plateaus.
    
    Returns:
        float: The minimum change in SD to consider stable.
    """
    return get_config()['stability_threshold']