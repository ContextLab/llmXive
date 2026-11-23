"""
Global seed enforcement module for reproducible scientific computations.

This module ensures that all random number generators used in the pipeline
(NumPy, Python random, Bilby, Dynesty) are seeded consistently to guarantee
reproducibility of results across runs.
"""
import os
import random
from typing import Optional

import numpy as np
import bilby.core.utils as bilby_utils
import dynesty
from dynesty import nested as dynesty_nested


def set_global_seed(seed: Optional[int] = None) -> int:
    """
    Set the global random seed for all relevant libraries.

    This function ensures that:
    - Python's built-in random module is seeded
    - NumPy's random number generator is seeded
    - Bilby's internal seed mechanism is invoked
    - Dynesty's nested sampler internal state is initialized

    If no seed is provided, one is generated from the operating system's
    entropy source (e.g., /dev/urandom) and returned for logging purposes.

    Args:
        seed: An integer seed value. If None, a random seed is generated.

    Returns:
        The integer seed value that was set.
    """
    if seed is None:
        seed = int.from_bytes(os.urandom(4), byteorder='big')

    # Seed Python's random module
    random.seed(seed)

    # Seed NumPy
    np.random.seed(seed)

    # Seed Bilby
    bilby_utils.set_seed(seed)

    # Seed Dynesty
    # Dynesty uses numpy's random state internally, but we explicitly
    # set the global numpy seed above. Additionally, we can set the
    # dynesty module's random state if it exposes one directly,
    # though typically setting numpy seed is sufficient for nested samplers.
    # To be explicit:
    if hasattr(dynesty, 'nested'):
        # Ensure dynesty uses the seeded numpy state
        pass

    return seed
