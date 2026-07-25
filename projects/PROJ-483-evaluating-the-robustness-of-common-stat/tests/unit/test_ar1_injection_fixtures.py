"""
Specific fixtures and helpers for AR(1) injection validation tests.
Supports T009 requirements for mock data fixtures.
"""
import numpy as np
from typing import Tuple

def create_ar1_process(
    n: int, 
    phi: float, 
    sigma: float = 1.0, 
    seed: int = 42
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Creates a synthetic AR(1) process for validation.
    This is used to verify that the injection logic produces the expected
    autocorrelation structure.
    
    Args:
        n: Length of the series.
        phi: Autocorrelation coefficient (0 <= phi < 1).
        sigma: Standard deviation of the innovation noise.
        seed: Random seed.
        
    Returns:
        Tuple containing (generated_series, theoretical_acf).
    """
    rng = np.random.default_rng(seed)
    eps = rng.normal(0, sigma, n)
    x = np.zeros(n)
    x[0] = eps[0]
    for t in range(1, n):
        x[t] = phi * x[t-1] + eps[t]
    return x, eps
