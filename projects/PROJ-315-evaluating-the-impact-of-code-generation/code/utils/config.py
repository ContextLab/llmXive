"""
Configuration management for the research pipeline.

Handles environment variables, random seed pinning, and global settings.
Ensures reproducibility by pinning seeds for numpy, pandas, and sklearn.
"""
import os
import random
from typing import Any, Dict, Optional
import numpy as np
import pandas as pd
import sklearn

# Default seed
DEFAULT_SEED = 42

def get_seed() -> int:
    """
    Get the random seed from environment variable or default.
    
    Returns:
        int: The seed value.
    """
    seed_str = os.getenv("RESEARCH_SEED", str(DEFAULT_SEED))
    try:
        return int(seed_str)
    except ValueError:
        return DEFAULT_SEED

def set_global_seed(seed: Optional[int] = None) -> None:
    """
    Set global random seeds for reproducibility.
    
    Sets seeds for:
    - Python random
    - NumPy
    - Pandas (via numpy)
    - Scikit-learn (via numpy and explicit functions if available)
    
    Args:
        seed: Seed value. Defaults to RESEARCH_SEED env var or 42.
    """
    if seed is None:
        seed = get_seed()
        
    # Python random
    random.seed(seed)
    
    # NumPy
    np.random.seed(seed)
    
    # Pandas (uses numpy)
    pd.options.mode.chained_assignment = None  # Suppress warnings
    
    # Scikit-learn
    # sklearn.utils.check_random_state(seed) ensures random state consistency
    # for functions that accept random_state.
    # For global consistency, we ensure numpy is seeded (done above).
    # Some sklearn functions use numpy.random directly.
    
    # Explicitly set sklearn random state if accessible (for older versions)
    if hasattr(sklearn, 'random_state'):
        sklearn.random_state = seed
        
    # Ensure any sklearn estimator default random_state uses our seed if not specified
    # This is handled by setting numpy seed, but we can also patch if needed.
    # For now, numpy seed is the primary mechanism for sklearn.
    
    # Log seed setting
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Global seed set to {seed}")

def load_config_from_env() -> Dict[str, Any]:
    """
    Load configuration from environment variables.
    
    Returns:
        Dict of configuration values.
    """
    return {
        "seed": get_seed(),
        "data_path": os.getenv("DATA_PATH", "data/raw"),
        "output_path": os.getenv("OUTPUT_PATH", "data/processed"),
        "min_group_size": int(os.getenv("MIN_GROUP_SIZE", "500")),
        "completeness_threshold": float(os.getenv("COMPLETENESS_THRESHOLD", "0.95"))
    }
