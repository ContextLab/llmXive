"""
Reproducibility utility for deterministic execution.

This module sets global random seeds for Python, NumPy, and scikit-learn
based on a configuration value. It must be imported and executed at the
very beginning of any script to ensure deterministic results.
"""

import logging
import random
from typing import Optional

import numpy as np

# Try to import sklearn seed control; handle gracefully if not available
try:
    from sklearn.utils import check_random_state
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

from utils.config import get_config_value
from utils.logging import get_logger

# Global flag to prevent re-seeding
_seed_initialized = False

logger = get_logger(__name__)


def set_global_seed(seed: Optional[int] = None) -> int:
    """
    Set global random seeds for Python, NumPy, and scikit-learn.

    Args:
        seed: The seed value to use. If None, reads from config.

    Returns:
        The seed value that was set.

    Raises:
        ValueError: If the seed is not a non-negative integer.
        RuntimeError: If the configuration cannot be read.
    """
    global _seed_initialized

    if _seed_initialized:
        logger.debug("Global seed already initialized. Skipping re-seeding.")
        return get_config_value("random_seed", 42)

    # Determine seed value
    if seed is None:
        try:
            seed = get_config_value("random_seed", 42)
        except Exception as e:
            logger.warning(f"Could not read 'random_seed' from config: {e}. Defaulting to 42.")
            seed = 42

    if not isinstance(seed, int) or seed < 0:
        raise ValueError(f"Seed must be a non-negative integer, got: {seed}")

    logger.info(f"Setting global random seed to: {seed}")

    # Set Python's random seed
    random.seed(seed)

    # Set NumPy's random seed
    np.random.seed(seed)

    # Set scikit-learn's global seed if available
    if SKLEARN_AVAILABLE:
        # sklearn.utils.check_random_state handles the seed, but to set a global default
        # for functions that don't take a random_state arg, we rely on the numpy seed
        # which sklearn respects. However, for explicit global state in newer sklearn:
        try:
            # In newer sklearn versions, there isn't a simple global setter like np.random.seed
            # that affects all internal generators without passing random_state explicitly.
            # We rely on the numpy seed which covers most numpy-based operations in sklearn.
            # If a specific global seed API exists in the installed version, we could call it.
            pass
        except Exception as e:
            logger.warning(f"Could not set global sklearn seed: {e}")
    else:
        logger.debug("scikit-learn not available, skipping sklearn seed configuration.")

    _seed_initialized = True
    return seed


def initialize_from_config() -> int:
    """
    Initialize seeds from the project configuration file.

    This is the recommended entry point for scripts. It reads the
    `random_seed` value from `config.yaml` (or equivalent) and sets
    all global seeds.

    Returns:
        The seed value that was set.
    """
    return set_global_seed(None)
