import numpy as np
from numba import njit, prange
from typing import Tuple, Optional
import logging
import os

# Configure logger
logger = logging.getLogger(__name__)

@njit(fastmath=True, cache=True)
def _sample_entropy_core(signal: np.ndarray, m: int, r: float) -> float:
    """
    Core Numba-optimized Sample Entropy calculation.
    Computes the negative natural log of the conditional probability that
    two sequences similar for m points remain similar at m+1 points.
    """
    n = len(signal)
    if n < m + 2:
        return np.nan

    # Normalize signal for stability
    mean_val = np.mean(signal)
    std_val = np.std(signal)
    if std_val == 0:
        return 0.0
    
    # Use a local copy to avoid modifying input, though numba handles this well
    # We work on the raw array to avoid overhead
    # To save memory, we compute distances on the fly without full matrix

    count_m = 0.0
    count_m1 = 0.0

    # Pre-allocate buffer for distances if needed, but we'll do it inline
    # Iterate over all pairs (i, j) with i < j
    for i in range(n - m):
        # Extract template i
        # We don't slice to avoid copy overhead, just index
        # Check max distance for template i against all j > i
        
        # Optimization: We can't easily vectorize the inner loop in numba without creating arrays,
        # but numba loops are fast.
        
        for j in range(i + 1, n - m):
            # Compute max absolute difference for length m
            max_diff = 0.0
            for k in range(m):
                diff = abs(signal[i + k] - signal[j + k])
                if diff > max_diff:
                    max_diff = diff
            
            if max_diff < r:
                count_m += 1.0
                
                # Now check for length m+1
                max_diff_m1 = max_diff
                # Check the next point
                if i + m < n and j + m < n:
                    diff_next = abs(signal[i + m] - signal[j + m])
                    if diff_next < r:
                        count_m1 += 1.0

    if count_m == 0:
        return np.nan
    if count_m1 == 0:
        return -np.log(0.0) # Should be infinity, but we return nan or large number
    
    return -np.log(count_m1 / count_m)

@njit(fastmath=True, cache=True)
def _approximate_entropy_core(signal: np.ndarray, m: int, r: float) -> float:
    """
    Core Numba-optimized Approximate Entropy calculation.
    Computes the logarithm of the ratio of the frequency of similar templates
    of length m to those of length m+1.
    """
    n = len(signal)
    if n < m + 1:
        return np.nan

    # Normalize
    mean_val = np.mean(signal)
    std_val = np.std(signal)
    if std_val == 0:
        return 0.0

    # Count matches for length m
    count_m = 0.0
    for i in range(n - m + 1):
        for j in range(n - m + 1):
            if i == j:
                continue
            max_diff = 0.0
            for k in range(m):
                diff = abs(signal[i + k] - signal[j + k])
                if diff > max_diff:
                    max_diff = diff
            if max_diff < r:
                count_m += 1.0
    
    # Count matches for length m+1
    count_m1 = 0.0
    for i in range(n - m):
        for j in range(n - m):
            if i == j:
                continue
            max_diff = 0.0
            for k in range(m + 1):
                diff = abs(signal[i + k] - signal[j + k])
                if diff > max_diff:
                    max_diff = diff
            if max_diff < r:
                count_m1 += 1.0

    if count_m == 0 or count_m1 == 0:
        return np.nan

    phi_m = count_m / (n - m + 1) / (n - m)
    phi_m1 = count_m1 / (n - m) / (n - m - 1)
    
    if phi_m == 0 or phi_m1 == 0:
        return np.nan

    return np.log(phi_m) - np.log(phi_m1)

def sample_entropy(signal: np.ndarray, m: int = 2, r: Optional[float] = None) -> float:
    """
    Compute Sample Entropy (SampEn) of a 1D signal.
    
    Parameters:
    -----------
    signal : np.ndarray
        1D array of time series data.
    m : int
        Template length (default 2).
    r : float, optional
        Tolerance threshold. If None, defaults to 0.2 * std(signal).
        
    Returns:
    --------
    float
        Sample Entropy value. Returns np.nan if computation fails.
    """
    if not isinstance(signal, np.ndarray):
        signal = np.array(signal, dtype=np.float64)
    else:
        signal = signal.astype(np.float64)
        
    if signal.ndim != 1:
        raise ValueError("Signal must be 1-dimensional.")
        
    if len(signal) < m + 2:
        logger.warning(f"Signal length {len(signal)} is too short for m={m}.")
        return np.nan

    if r is None:
        std_val = np.std(signal)
        if std_val == 0:
            return 0.0
        r = 0.2 * std_val
    
    # Call the JIT-compiled core
    try:
        result = _sample_entropy_core(signal, m, r)
        return float(result)
    except Exception as e:
        logger.error(f"Error in sample entropy calculation: {e}")
        return np.nan

def approximate_entropy(signal: np.ndarray, m: int = 2, r: Optional[float] = None) -> float:
    """
    Compute Approximate Entropy (ApEn) of a 1D signal.
    
    Parameters:
    -----------
    signal : np.ndarray
        1D array of time series data.
    m : int
        Template length (default 2).
    r : float, optional
        Tolerance threshold. If None, defaults to 0.2 * std(signal).
        
    Returns:
    --------
    float
        Approximate Entropy value. Returns np.nan if computation fails.
    """
    if not isinstance(signal, np.ndarray):
        signal = np.array(signal, dtype=np.float64)
    else:
        signal = signal.astype(np.float64)
        
    if signal.ndim != 1:
        raise ValueError("Signal must be 1-dimensional.")
        
    if len(signal) < m + 1:
        logger.warning(f"Signal length {len(signal)} is too short for m={m}.")
        return np.nan

    if r is None:
        std_val = np.std(signal)
        if std_val == 0:
            return 0.0
        r = 0.2 * std_val

    try:
        result = _approximate_entropy_core(signal, m, r)
        return float(result)
    except Exception as e:
        logger.error(f"Error in approximate entropy calculation: {e}")
        return np.nan

def compute_entropy_metrics(signal: np.ndarray, m: int = 2, r: Optional[float] = None) -> dict:
    """
    Compute both Sample Entropy and Approximate Entropy for a signal.
    
    Parameters:
    -----------
    signal : np.ndarray
        1D array of time series data.
    m : int
        Template length.
    r : float, optional
        Tolerance threshold.
        
    Returns:
    --------
    dict
        Dictionary with keys 'sample_entropy' and 'approximate_entropy'.
    """
    se = sample_entropy(signal, m, r)
    ae = approximate_entropy(signal, m, r)
    return {
        'sample_entropy': se,
        'approximate_entropy': ae
    }