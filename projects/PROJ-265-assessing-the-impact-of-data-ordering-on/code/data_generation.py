"""
Data generation module for synthetic time series.

Provides functions to generate autoregressive (AR) processes and other
synthetic datasets for bootstrap analysis.
"""
import numpy as np
from typing import Union, Optional
from config import get_data_seed


def generate_ar1(phi: float, n: int, seed: Optional[int] = None) -> np.ndarray:
    """
    Generate an AR(1) time series: y_t = phi * y_{t-1} + epsilon.
    
    Args:
        phi: Autoregressive coefficient (|phi| < 1 for stationarity).
        n: Length of the time series to generate.
        seed: Random seed for reproducibility. If None, uses config default.
    
    Returns:
        numpy.ndarray: Generated time series of length n.
    
    Raises:
        ValueError: If |phi| >= 1.
    """
    if seed is None:
        seed = get_data_seed()
    
    if abs(phi) >= 1.0:
        raise ValueError(f"phi must be < 1 in magnitude for stationarity, got {phi}")
    
    rng = np.random.default_rng(seed)
    epsilon = rng.normal(0, 1, n)
    
    y = np.zeros(n)
    y[0] = epsilon[0] / np.sqrt(1 - phi**2)  # Stationary initialization
    
    for t in range(1, n):
        y[t] = phi * y[t-1] + epsilon[t]
    
    return y
