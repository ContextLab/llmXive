"""
Effective sample size (Neff) calculation module.

Implements the method of Pyper & Peterman for correcting p-values for autocorrelation.
Formula: Neff = N * (1 - rho_1) / (1 + rho_1)
Where rho_1 is the lag-1 autocorrelation of the detrended time series.
"""
import numpy as np
from scipy import signal
from typing import Union
import pandas as pd
from code import logger

def calculate_neff(time_series: Union[pd.Series, np.ndarray]) -> float:
    """
    Calculate the effective sample size (Neff) for a given time series.
    
    Steps:
    1. Detrend the series using scipy.signal.detrend (removes linear trend).
    2. Calculate lag-1 autocorrelation (rho_1) of the residuals.
    3. Apply formula: Neff = N * (1 - rho_1) / (1 + rho_1)
    
    Args:
        time_series: 1D array-like or pandas Series.
        
    Returns:
        Effective sample size (float).
        
    Raises:
        ValueError: If the series is too short or has no variance.
    """
    # Convert to numpy array
    x = np.asarray(time_series)
    n = len(x)
    
    if n < 3:
        raise ValueError(f"Series too short for Neff calculation: {n} points")
    
    # Step 1: Detrend
    # scipy.signal.detrend removes the linear trend by default
    detrended = signal.detrend(x)
    
    # Check for zero variance after detrending
    if np.std(detrended) < 1e-10:
        logger.warning("Detrended series has near-zero variance. Neff may be unreliable.")
        return float(n)
    
    # Step 2: Calculate lag-1 autocorrelation (rho_1) of the residuals
    # We calculate this manually to ensure we use the detrended residuals
    mean_val = np.mean(detrended)
    centered = detrended - mean_val
    
    # Numerator: sum of (x_t * x_{t+1}) for centered data
    # Denominator: sum of (x_t^2) for centered data
    # This is the standard definition of autocorrelation at lag 1
    numerator = np.sum(centered[:-1] * centered[1:])
    denominator = np.sum(centered ** 2)
    
    if denominator == 0:
        logger.warning("Zero variance in centered detrended series. Returning N.")
        return float(n)
        
    rho_1 = numerator / denominator
    
    # Ensure rho_1 is within [-1, 1] to avoid numerical issues in the formula
    rho_1 = np.clip(rho_1, -0.999, 0.999)
    
    # Step 3: Apply Pyper & Peterman formula
    # Neff = N * (1 - rho_1) / (1 + rho_1)
    neff = n * (1 - rho_1) / (1 + rho_1)
    
    logger.debug(f"Neff calculation: N={n}, rho_1={rho_1:.4f}, Neff={neff:.2f}")
    
    return float(neff)