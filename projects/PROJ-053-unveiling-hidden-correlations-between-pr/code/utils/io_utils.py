"""
Utility module for I/O and global provenance settings.

This module sets global random seeds for reproducibility across the
project. It imports the project-wide random seed from ``config`` and
applies it to both ``numpy`` and Python's built‑in ``random`` modules.
The seed is set at import time, ensuring that any subsequent random
operations are deterministic without requiring the caller to remember
to seed manually.
"""

import random
import numpy as np

from config import get_random_seed, get_logger

# Initialise a logger for this module (optional but useful for debugging)
log = get_logger(__name__)

def set_global_seeds(seed: int | None = None) -> None:
    """
    Set the global random seeds for ``numpy`` and ``random``.

    Parameters
    ----------
    seed : int | None
        The seed to use. If ``None`` the seed is obtained from
        ``config.get_random_seed()``. The default seed defined in the
        configuration is ``42`` (see ``config.get_random_seed``).

    This function is idempotent – calling it multiple times with the same
    seed will reset the RNG state to the same deterministic point.
    """
    if seed is None:
        seed = get_random_seed()
    log.debug("Setting global random seeds to %s", seed)
    random.seed(seed)
    np.random.seed(seed)

# Apply seeds immediately when the module is imported so that any
# downstream code that imports ``io_utils`` gets a reproducible RNG state.
set_global_seeds()
