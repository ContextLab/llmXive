"""
Synthetic data generation module for fGn and ARFIMA processes.
Includes robustness checks for mean deviation and retry mechanisms.
"""
import numpy as np
import pandas as pd
from typing import List, Union, Optional, Tuple, Dict, Any
from scipy import stats
from scipy.signal import fftconvolve
import logging
import random

from src.utils.config import set_seed
from src.utils.logging import log_info, log_warning, log_error, log_critical

# Configure logger
logger = logging.getLogger(__name__)

# Constants
MAX_RETRY_ATTEMPTS = 3
MAX_MEAN_DEVIATION = 0.01
DEFAULT_LENGTH = 1000
DEFAULT_HURST = 0.7
DEFAULT_SEED = 42

class SyntheticGenerationError(Exception):
    """Custom exception for synthetic generation failures."""
    pass

def _generate_fgn_base(hurst: float, length: int, seed: int) -> np.ndarray:
    """
    Generate fractional Gaussian noise using the Davies-Harte algorithm (approximation).
    Uses FFT-based method for efficiency.

    Args:
        hurst: Hurst exponent (0 < H < 1)
        length: Number of points to generate
        seed: Random seed for reproducibility

    Returns:
        np.ndarray: Generated fGn series
    """
    set_seed(seed)
    n = length
    # Ensure n is a power of 2 for FFT efficiency (pad if necessary)
    n_fft = 1
    while n_fft < 2 * n - 1:
        n_fft *= 2

    # Create the covariance function for fGn
    # C(k) = 0.5 * (|k+1|^(2H) - 2|k|^(2H) + |k-1|^(2H))
    k = np.arange(n_fft)
    cov = 0.5 * (np.abs(k + 1) ** (2 * hurst) - 2 * np.abs(k) ** (2 * hurst) + np.abs(k - 1) ** (2 * hurst))
    cov[0] = 1.0  # Variance is 1

    # FFT of covariance
    fft_cov = np.fft.fft(cov)
    # Ensure non-negative (numerical stability)
    fft_cov = np.maximum(fft_cov, 0)

    # Generate complex Gaussian noise
    real = np.random.normal(0, 1, n_fft)
    imag = np.random.normal(0, 1, n_fft)
    z = real + 1j * imag

    # Scale by sqrt of FFT covariance
    w = np.sqrt(fft_cov) * z

    # Inverse FFT to get the series
    series = np.fft.ifft(w).real

    # Take the first n points
    return series[:n]

def generate_fgn(hurst: float, length: int, seed: int, max_mean_deviation: float = MAX_MEAN_DEVIATION, max_attempts: int = MAX_RETRY_ATTEMPTS) -> Tuple[np.ndarray, int]:
    """
    Generate fractional Gaussian noise with a robustness check for mean deviation.
    If the generated series mean deviates significantly from zero, retry with a new seed.

    Args:
        hurst: Hurst exponent (0 < H < 1)
        length: Number of points to generate
        seed: Initial random seed
        max_mean_deviation: Maximum allowed deviation of the mean from 0
        max_attempts: Maximum number of retry attempts

    Returns:
        Tuple[np.ndarray, int]: Generated fGn series and the seed used
    """
    if not (0 < hurst < 1):
        raise SyntheticGenerationError(f"Hurst exponent must be between 0 and 1, got {hurst}")
    if length < 10:
        raise SyntheticGenerationError(f"Length must be at least 10, got {length}")

    current_seed = seed
    for attempt in range(max_attempts):
        try:
            series = _generate_fgn_base(hurst, length, current_seed)
            current_mean = np.mean(series)

            if abs(current_mean) <= max_mean_deviation:
                log_info(f"Generated fGn series (H={hurst}, L={length}) with mean={current_mean:.6f} (seed={current_seed}) - PASS")
                return series, current_seed
            else:
                log_warning(f"Attempt {attempt + 1}: Generated fGn series mean={current_mean:.6f} exceeds threshold {max_mean_deviation}. Retrying with new seed.")
                # Increment seed for next attempt to ensure different random sequence
                current_seed += 1
        except Exception as e:
            log_error(f"Attempt {attempt + 1} failed with error: {str(e)}")
            current_seed += 1

    raise SyntheticGenerationError(
        f"Failed to generate fGn series with mean within {max_mean_deviation} after {max_attempts} attempts. "
        f"Last mean deviation: {abs(np.mean(series)) if 'series' in locals() else 'N/A'}"
    )

def generate_synthetic_series(
    hurst: float = DEFAULT_HURST,
    length: int = DEFAULT_LENGTH,
    seed: int = DEFAULT_SEED,
    max_mean_deviation: float = MAX_MEAN_DEVIATION,
    max_attempts: int = MAX_RETRY_ATTEMPTS
) -> pd.DataFrame:
    """
    Generate a synthetic series (fGn) with robustness checks.

    Args:
        hurst: Hurst exponent
        length: Length of the series
        seed: Random seed
        max_mean_deviation: Maximum allowed mean deviation
        max_attempts: Maximum retry attempts

    Returns:
        pd.DataFrame: DataFrame with 'timestamp', 'value', 'series_id'
    """
    series, used_seed = generate_fgn(hurst, length, seed, max_mean_deviation, max_attempts)

    # Create DataFrame
    df = pd.DataFrame({
        'timestamp': pd.date_range(start='2020-01-01', periods=length, freq='D'),
        'value': series,
        'series_id': f"synthetic_H{hurst}_L{length}_S{used_seed}"
    })

    return df

def shuffle_series(series: np.ndarray, seed: Optional[int] = None) -> np.ndarray:
    """
    Shuffle a series to create a null distribution.

    Args:
        series: Input series
        seed: Optional seed for reproducibility

    Returns:
        np.ndarray: Shuffled series
    """
    if seed is not None:
        np.random.seed(seed)
    shuffled = series.copy()
    np.random.shuffle(shuffled)
    return shuffled

def compute_acf_lag1(series: np.ndarray) -> float:
    """
    Compute the first lag autocorrelation.

    Args:
        series: Input series

    Returns:
        float: ACF at lag 1
    """
    if len(series) < 2:
        return 0.0
    return stats.correlation(series[:-1], series[1:])

def generate_null_distributions(
    series: np.ndarray,
    n_shuffles: int = 1000,
    seed: int = DEFAULT_SEED
) -> List[np.ndarray]:
    """
    Generate null distributions by shuffling the series.

    Args:
        series: Input series
        n_shuffles: Number of shuffles
        seed: Random seed

    Returns:
        List[np.ndarray]: List of shuffled series
    """
    np.random.seed(seed)
    nulls = []
    for i in range(n_shuffles):
        nulls.append(shuffle_series(series, seed=seed + i))
    return nulls

def generate_synthetic_grid(
    hurst_values: List[float] = [0.5, 0.7, 0.8, 0.9],
    lengths: List[int] = [100, 500, 1000, 5000, 10000],
    base_seed: int = DEFAULT_SEED,
    max_mean_deviation: float = MAX_MEAN_DEVIATION,
    max_attempts: int = MAX_RETRY_ATTEMPTS
) -> List[pd.DataFrame]:
    """
    Generate a grid of synthetic series for various H and length combinations.

    Args:
        hurst_values: List of Hurst exponents
        lengths: List of series lengths
        base_seed: Base seed for the grid
        max_mean_deviation: Maximum allowed mean deviation
        max_attempts: Maximum retry attempts

    Returns:
        List[pd.DataFrame]: List of generated DataFrames
    """
    dfs = []
    seed_counter = base_seed

    for h in hurst_values:
        for l in lengths:
            try:
                df = generate_synthetic_series(
                    hurst=h,
                    length=l,
                    seed=seed_counter,
                    max_mean_deviation=max_mean_deviation,
                    max_attempts=max_attempts
                )
                dfs.append(df)
                seed_counter += 1
            except SyntheticGenerationError as e:
                log_error(f"Failed to generate series for H={h}, L={l}: {str(e)}")
                # Continue to next combination rather than failing the whole grid

    return dfs

def main():
    """
    Main function to demonstrate synthetic generation with robustness checks.
    """
    log_info("Starting synthetic generation demo with robustness checks...")

    # Test robustness with boundary H values
    test_cases = [
        {"hurst": 0.5, "length": 1000, "seed": 42},
        {"hurst": 0.9, "length": 1000, "seed": 43},
        {"hurst": 0.51, "length": 500, "seed": 44},
        {"hurst": 0.89, "length": 500, "seed": 45}
    ]

    for i, case in enumerate(test_cases):
        try:
            df = generate_synthetic_series(
                hurst=case["hurst"],
                length=case["length"],
                seed=case["seed"]
            )
            log_info(f"Test case {i+1}: H={case['hurst']}, L={case['length']} - SUCCESS")
            log_info(f"  Mean: {df['value'].mean():.6f}")
            log_info(f"  Std: {df['value'].std():.6f}")
            log_info(f"  Series ID: {df['series_id'].iloc[0]}")
        except SyntheticGenerationError as e:
            log_critical(f"Test case {i+1}: H={case['hurst']}, L={case['length']} - FAILED: {str(e)}")

    log_info("Synthetic generation demo completed.")

if __name__ == "__main__":
    main()