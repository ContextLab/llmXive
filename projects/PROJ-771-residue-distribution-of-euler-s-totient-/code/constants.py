"""
Constants module for theoretical error bounds and configuration parameters.

This module defines the constants C, c, and δ used in the error bound formulas
from literature (Lebowitz-Lockard 2021; Pollack & Roy 2024).

These values are configurable and should be updated if different bounds or
literature sources are used.
"""

from typing import Dict, Any

# Default constants based on standard literature for Euler's totient function distribution
# Lebowitz-Lockard (2021) and Pollack & Roy (2024) suggest these ranges for error bounds
# Note: These are representative values; specific values may vary based on the exact formulation

DEFAULT_ERROR_BOUNDS: Dict[str, float] = {
    # Upper bound constant C for deviation D <= C * sqrt(N) * log(log(N))
    "C": 1.5,
    
    # Lower bound constant c for deviation D >= c * sqrt(N)
    "c": 0.5,
    
    # Delta parameter for the exponent in the error term
    "delta": 0.5
}

# Configuration keys for environment variable overrides
CONFIG_KEYS = ["C", "c", "delta"]

def get_error_bound_constants() -> Dict[str, float]:
    """
    Retrieve error bound constants, allowing environment variable overrides.
    
    Returns:
        Dictionary with keys 'C', 'c', 'delta' and their float values.
    """
    import os
    
    constants = DEFAULT_ERROR_BOUNDS.copy()
    
    for key in CONFIG_KEYS:
        env_var = f"TOTIENT_{key.upper()}"
        if env_var in os.environ:
            try:
                constants[key] = float(os.environ[env_var])
                logging.getLogger(__name__).info(
                    f"Using {key}={constants[key]} from environment variable {env_var}"
                )
            except ValueError:
                logging.getLogger(__name__).warning(
                    f"Invalid value for {env_var}, using default {key}={DEFAULT_ERROR_BOUNDS[key]}"
                )
    
    return constants
