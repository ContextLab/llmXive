"""
Minimal shim for the `pyDOE` package to satisfy the `pwlf` dependency.

The `pwlf` library imports `lhs` (Latin Hypercube Sampling) from `pyDOE`.
For the purposes of piecewise linear regression we only need a callable
that returns a NumPy array of shape (n_samples, n_factors) with values in
the interval [0, 1).  A simple implementation based on `numpy.random`
provides sufficient functionality for the regression routine without
pulling in the full external dependency.
"""

from __future__ import annotations

import numpy as np
from typing import Tuple

def lhs(
    n: int,
    samples: int,
    criterion: str | None = None,
    iterations: int = 0,
) -> np.ndarray:
    """
    Generate a Latin Hypercube Sample (LHS) matrix.

    Parameters
    ----------
    n : int
        Number of factors (dimensions).
    samples : int
        Number of sample points to generate.
    criterion : str, optional
        Ignored in this shim – present for API compatibility.
    iterations : int, optional
        Ignored – present for API compatibility.

    Returns
    -------
    np.ndarray
        An array of shape (samples, n) with values in the half‑open
        interval [0.0, 1.0).  Each column contains a stratified random
        permutation of the intervals [(i-1)/samples, i/samples) for i in
        1..samples.
    """
    # Create the stratified intervals for each dimension
    cut = np.linspace(0, 1, samples + 1)

    # Randomly place a point within each interval for each dimension
    # and then shuffle the rows.
    result = np.empty((samples, n), dtype=float)
    for i in range(n):
        # Uniform points within each interval
        points = cut[:-1] + np.random.rand(samples) * (cut[1:] - cut[:-1])
        np.random.shuffle(points)
        result[:, i] = points

    return result

__all__: Tuple[str, ...] = ("lhs",)