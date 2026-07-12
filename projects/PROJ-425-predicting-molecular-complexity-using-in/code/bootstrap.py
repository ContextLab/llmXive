"""
Bootstrap resampling utilities.

Provides a simple function to perform bootstrap resampling on a list of numeric
values and compute the mean of each resampled dataset. This is used by the unit
test in `tests/unit/test_analysis.py` to verify basic bootstrap functionality.
"""

import random
from typing import List, Sequence

# Optional: seed for reproducibility can be set by the caller if desired.

def bootstrap_resample(data: Sequence[float], n_iter: int = 100) -> List[float]:
    """
    Perform bootstrap resampling on the provided data.

    Parameters
    ----------
    data: Sequence[float]
        The original dataset to resample from.
    n_iter: int, default 100
        Number of bootstrap iterations.

    Returns
    -------
    List[float]
        List of means computed from each bootstrap sample.
    """
    if not data:
        raise ValueError("Input data for bootstrap resampling must be non-empty.")
    if n_iter <= 0:
        raise ValueError("n_iter must be a positive integer.")

    data_list = list(data)
    n = len(data_list)
    results: List[float] = []
    for _ in range(n_iter):
        # Sample with replacement
        sample = [random.choice(data_list) for _ in range(n)]
        results.append(sum(sample) / n)
    return results
