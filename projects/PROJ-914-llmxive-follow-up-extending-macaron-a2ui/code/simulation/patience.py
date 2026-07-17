"""
User Patience Modeling for Simulation.

Implements FR-003: Model user abandonment using exponential decay.
"""

import numpy as np
from typing import Optional

# Ensure reproducibility via global seed configuration if needed,
# though specific seeds should be passed or managed by the runner.
# Default mean patience time in seconds as per spec (FR-003).
DEFAULT_MEAN_PATIENCE_SECONDS: float = 2.0

def sample_patience(
    mean_seconds: float = DEFAULT_MEAN_PATIENCE_SECONDS,
    rng: Optional[np.random.Generator] = None
) -> float:
    """
    Sample a user patience threshold from an exponential distribution.

    This models the time (in seconds) a user is willing to wait for a response
    before abandoning the interaction. The distribution is exponential with
    a specified mean (lambda = 1 / mean_seconds).

    Args:
        mean_seconds: The mean wait time (scale parameter) in seconds.
                      Default is 2.0 seconds per FR-003.
        rng: A numpy random Generator instance for reproducibility.
             If None, a new Generator is created (non-deterministic).

    Returns:
        float: The sampled patience threshold in seconds.
    """
    if mean_seconds <= 0:
        raise ValueError(f"mean_seconds must be positive, got {mean_seconds}")

    if rng is None:
        # Fallback to global state if no generator provided, though explicit
        # injection is preferred for deterministic simulation runs.
        return np.random.exponential(scale=mean_seconds)
    
    return rng.exponential(scale=mean_seconds)
