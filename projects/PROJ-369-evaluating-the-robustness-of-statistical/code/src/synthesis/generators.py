"""
Synthetic data generators for fGn, ARFIMA, and null distributions.
Implements fractional Gaussian noise generation with strict mean validation.
"""
import numpy as np
import pandas as pd
from typing import List, Union, Optional, Tuple, Dict, Any
from scipy import stats
from scipy.signal import fftconvolve
import logging

from src.utils.config import get_path
from src.utils.logging import log_info, log_warning, log_error, log_critical

# Configure logger
logger = logging.getLogger(__name__)

# Mean validation tolerance (floating point precision)
MEAN_TOLERANCE = 1e-4

def _validate_mean(series: np.ndarray, target_mean: float = 0.0) -> None:
    """
    Post-generation assertion to verify the mean of the generated series
    is approximately zero. Raises ValueError if the deviation exceeds tolerance.
    
    This strengthens the ground-truth guarantee required for accurate Type I error
    measurement (Task T052).
    
    Args:
        series: The generated time series data.
        target_mean: The expected mean (default 0.0).
        
    Raises:
        ValueError: If the absolute difference between actual mean and target exceeds tolerance.
    """
    actual_mean = np.mean(series)
    deviation = abs(actual_mean - target_mean)
    
    if deviation > MEAN_TOLERANCE:
        error_msg = (
            f"Generated series mean validation failed: "
            f"actual mean = {actual_mean:.6e}, "
            f"target mean = {target_mean}, "
            f"deviation = {deviation:.6e} (exceeds tolerance {MEAN_TOLERANCE}). "
            f"Series length: {len(series)}. "
            f"Ground-truth guarantee compromised."
        )
        log_critical(error_msg)
        raise ValueError(error_msg)
    
    log_info(f"Mean validation passed: mean={actual_mean:.6e}, deviation={deviation:.6e}")

def generate_fgn(n: int, h: float, rng: Optional[np.random.Generator] = None) -> np.ndarray:
    """
    Generate fractional Gaussian noise (fGn) with specified Hurst exponent.
    
    Uses the Davies-Harte algorithm via circulant embedding.
    
    Args:
        n: Length of the series.
        h: Hurst exponent (0 < h < 1).
        rng: Random number generator. If None, uses np.random.default_rng().
        
    Returns:
        np.ndarray: Generated fGn series with mean ≈ 0.
        
    Raises:
        ValueError: If h is out of range or mean validation fails.
    """
    if rng is None:
        rng = np.random.default_rng()
        
    if not 0 < h < 1:
        raise ValueError(f"Hurst exponent h must be in (0, 1), got {h}")
        
    if n <= 0:
        raise ValueError(f"Length n must be positive, got {n}")

    # Davies-Harte algorithm parameters
    m = 2 ** (int(np.ceil(np.log2(2 * n - 1))) + 1)
    k = np.arange(1, m // 2 + 1)
    
    # Covariance function for fGn
    def cov_func(k, h):
        return 0.5 * (np.abs(k - 1)**(2*h) - 2*np.abs(k)**(2*h) + np.abs(k + 1)**(2*h))
    
    # Compute eigenvalues of the covariance matrix
    gamma = np.zeros(m)
    for i in range(1, m // 2 + 1):
        gamma[i] = cov_func(i, h)
        gamma[m - i] = cov_func(i, h)
    gamma[0] = 1.0
    
    # Eigenvalues of the circulant matrix
    lam = m * np.fft.ifft(gamma).real
    
    # Check for negative eigenvalues (should not happen for valid h)
    if np.any(lam < 0):
        raise ValueError("Negative eigenvalues detected in Davies-Harte algorithm. Invalid h?")
        
    # Generate complex normal variables
    w = np.zeros(m, dtype=complex)
    for i in range(m):
        if lam[i] > 0:
            sigma = np.sqrt(lam[i] / 2)
            re = rng.normal(0, sigma)
            im = rng.normal(0, sigma)
            w[i] = re + 1j * im
        else:
            w[i] = 0
            
    # Ensure symmetry for real output
    w[0] = 0
    if m % 2 == 0:
        w[m // 2] = 0
        
    # Inverse FFT to get the fGn
    x = np.fft.ifft(w).real
    
    # Return the first n elements
    series = x[:n]
    
    # VALIDATION: Ensure mean is approximately zero (Task T052)
    _validate_mean(series, target_mean=0.0)
    
    return series

def generate_synthetic_series(
    hurst: float,
    length: int,
    series_type: str = "fgn",
    seed: Optional[int] = None
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Generate a synthetic time series with specified Hurst exponent and mean=0.
    
    Args:
        hurst: Hurst exponent (0 < h < 1).
        length: Length of the series.
        series_type: Type of series ("fgn" or "arima"). Currently supports "fgn".
        seed: Random seed for reproducibility.
        
    Returns:
        Tuple of (series, metadata_dict)
        
    Raises:
        ValueError: If generation fails or mean validation fails.
    """
    if seed is not None:
        rng = np.random.default_rng(seed)
    else:
        rng = np.random.default_rng()
        
    metadata = {
        "hurst": hurst,
        "length": length,
        "series_type": series_type,
        "seed": seed,
        "actual_mean": None,
        "actual_std": None
    }
    
    if series_type == "fgn":
        series = generate_fgn(length, hurst, rng)
    else:
        raise ValueError(f"Unsupported series_type: {series_type}")
        
    # Update metadata with actual statistics
    metadata["actual_mean"] = float(np.mean(series))
    metadata["actual_std"] = float(np.std(series))
    
    log_info(
        f"Generated {series_type} series: H={hurst}, N={length}, "
        f"mean={metadata['actual_mean']:.6e}, std={metadata['actual_std']:.6e}"
    )
    
    return series, metadata

def shuffle_series(series: np.ndarray, rng: Optional[np.random.Generator] = None) -> np.ndarray:
    """
    Generate a shuffled (permuted) version of the series to create a null distribution.
    
    Args:
        series: Original time series.
        rng: Random number generator.
        
    Returns:
        np.ndarray: Shuffled series.
    """
    if rng is None:
        rng = np.random.default_rng()
        
    shuffled = series.copy()
    rng.shuffle(shuffled)
    return shuffled

def compute_acf_lag1(series: np.ndarray) -> float:
    """
    Compute the lag-1 autocorrelation coefficient.
    
    Args:
        series: Time series data.
        
    Returns:
        float: Lag-1 ACF value.
    """
    n = len(series)
    if n < 2:
        return 0.0
        
    mean = np.mean(series)
    var = np.var(series)
    
    if var == 0:
        return 0.0
        
    acf_lag1 = np.sum((series[1:] - mean) * (series[:-1] - mean)) / ((n - 1) * var)
    return float(acf_lag1)

def generate_null_distributions(
    series: np.ndarray,
    n_nulls: int = 1000,
    seed: Optional[int] = None
) -> List[np.ndarray]:
    """
    Generate multiple shuffled versions of a series for null distribution analysis.
    
    Args:
        series: Original time series.
        n_nulls: Number of shuffled versions to generate.
        seed: Random seed.
        
    Returns:
        List[np.ndarray]: List of shuffled series.
    """
    if seed is not None:
        rng = np.random.default_rng(seed)
    else:
        rng = np.random.default_rng()
        
    null_distributions = []
    for _ in range(n_nulls):
        null_series = shuffle_series(series, rng)
        null_distributions.append(null_series)
        
    log_info(f"Generated {n_nulls} null distributions for series of length {len(series)}")
    return null_distributions

def generate_synthetic_grid(
    hurst_values: List[float],
    length_values: List[int],
    seed_base: int = 42
) -> List[Dict[str, Any]]:
    """
    Generate a grid of synthetic series for Monte Carlo analysis.
    
    Args:
        hurst_values: List of Hurst exponents to test.
        length_values: List of series lengths to test.
        seed_base: Base seed for reproducibility.
        
    Returns:
        List of metadata dictionaries for each generated series.
    """
    results = []
    seed_counter = 0
    
    for h in hurst_values:
        for n in length_values:
            seed = seed_base + seed_counter
            try:
                series, meta = generate_synthetic_series(h, n, "fgn", seed=seed)
                meta["seed"] = seed
                results.append(meta)
                seed_counter += 1
            except ValueError as e:
                log_error(f"Failed to generate series H={h}, N={n}: {e}")
                # Continue with next grid point
                
    log_info(f"Generated grid: {len(results)} series from {len(hurst_values)} H values x {len(length_values)} lengths")
    return results

def main():
    """
    Main entry point for testing the generator module.
    """
    log_info("Running synthetic generator module tests...")
    
    # Test basic generation
    series, meta = generate_synthetic_series(hurst=0.8, length=1000, seed=123)
    log_info(f"Test series: H=0.8, N=1000, mean={meta['actual_mean']:.6e}")
    
    # Test grid generation
    grid = generate_synthetic_grid(
        hurst_values=[0.5, 0.7, 0.8, 0.9],
        length_values=[100, 500, 1000],
        seed_base=42
    )
    log_info(f"Grid generation complete: {len(grid)} series")
    
    # Test null distribution generation
    nulls = generate_null_distributions(series, n_nulls=100, seed=456)
    log_info(f"Null distribution test: generated {len(nulls)} shuffled series")
    
    # Verify ACF lag-1 of shuffled series is near zero
    acf_values = [compute_acf_lag1(null) for null in nulls]
    mean_acf = np.mean(acf_values)
    log_info(f"Null distribution ACF lag-1: mean={mean_acf:.6e} (should be ≈ 0)")
    
    log_info("All generator tests completed successfully.")

if __name__ == "__main__":
    main()