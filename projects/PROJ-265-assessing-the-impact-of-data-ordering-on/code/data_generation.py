import numpy as np
from typing import Union, Optional
from config import get_data_seed

def generate_ar1(phi: float, n: int, seed: int) -> np.ndarray:
    """
    Generate an AR(1) time series: y_t = phi * y_{t-1} + epsilon
    epsilon ~ N(0, 1)
    """
    np.random.seed(seed)
    y = np.zeros(n)
    # Initialize y_0
    y[0] = np.random.normal(0, 1)
    
    for t in range(1, n):
        epsilon = np.random.normal(0, 1)
        y[t] = phi * y[t-1] + epsilon
    
    return y
