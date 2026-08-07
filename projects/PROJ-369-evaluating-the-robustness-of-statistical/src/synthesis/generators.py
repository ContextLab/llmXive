"""
Synthetic data generation and shuffling utilities for the robustness study.

This module provides:
1. Generators for fractional Gaussian noise (fGn) and ARFIMA processes.
2. Metrics for theoretical VIF and N_eff.
3. Shuffling logic to create null distributions from real and synthetic series.
"""
import numpy as np
import pandas as pd
from scipy import stats
from scipy.stats import linregress
from typing import List, Dict, Any, Tuple, Optional, Union
import logging

from src.utils.config import set_seed

logger = logging.getLogger(__name__)


def generate_fgn(n: int, h: float, seed: Optional[int] = None) -> np.ndarray:
    """
    Generate fractional Gaussian noise (fGn) with Hurst exponent H.

    Uses the Davies-Harte algorithm (via circulant embedding) approximation.
    For simplicity and robustness, we use the Cholesky decomposition of the
    covariance matrix for moderate N, or a spectral method for larger N.
    Here we implement a spectral method using the circulant embedding approach.

    Args:
        n: Length of the series.
        h: Hurst exponent (0 < h < 1).
        seed: Random seed for reproducibility.

    Returns:
        numpy array of fGn.
    """
    if seed is not None:
        set_seed(seed)

    if h <= 0 or h >= 1:
        raise ValueError("Hurst exponent H must be in (0, 1).")

    # Covariance function for fGn: gamma(k) = 0.5 * (|k+1|^(2H) - 2|k|^(2H) + |k-1|^(2H))
    # We need to embed this in a circulant matrix of size 2n-2 (or 2n)
    m = 2 * n  # Size for circulant embedding
    k = np.arange(m)
    cov = 0.5 * (np.abs(k + 1)**(2 * h) - 2 * np.abs(k)**(2 * h) + np.abs(k - 1)**(2 * h))

    # The first n+1 values are the covariance of the fGn
    # The circulant matrix eigenvalues are the FFT of the first row
    # The first row of the circulant matrix is [gamma(0), gamma(1), ..., gamma(n-1), 0, gamma(n-1), ..., gamma(1)]
    # Actually, for Davies-Harte, we construct the vector:
    # lambda = [gamma(0), gamma(1), ..., gamma(n-1), 0, gamma(n-1), ..., gamma(1)]
    # But a simpler approach for this study is to use the spectral representation directly
    # or use a standard library if available. Since we rely on standard libs, let's use
    # the Cholesky method for smaller N and a spectral approximation for larger N if needed.
    # Given the constraints, let's use a robust spectral method.

    # Spectral method:
    # Generate complex normal variables with variance proportional to the spectral density
    # Spectral density of fGn is proportional to |w|^(1-2H) (singular at 0)
    # We'll use the circulant embedding method properly.

    # Construct the first row of the circulant matrix C
    # C[0] = gamma(0)
    # C[1..n-1] = gamma(1..n-1)
    # C[n] = 0 (to ensure positive definiteness in embedding)
    # C[n+1..2n-1] = gamma(n-1..1)
    r = np.zeros(m)
    r[:n] = cov[:n]
    r[n+1:] = cov[n-1:0:-1]

    # Eigenvalues of C are FFT of r
    lam = np.fft.fft(r)

    # Check for negative eigenvalues (failure of embedding)
    if np.any(lam < 0):
        # Fallback to Cholesky for small N, or increase m
        # For this implementation, we assume N is manageable or H is not extreme
        # If lam < 0, the embedding failed. We'll try a larger embedding size or use Cholesky.
        # Let's use Cholesky for reliability in this study context.
        return _fgn_cholesky(n, h, seed)

    sqrt_lam = np.sqrt(lam)
    z = np.random.randn(m) + 1j * np.random.randn(m)
    w = sqrt_lam * z
    x = np.fft.ifft(w).real
    return x[:n]


def _fgn_cholesky(n: int, h: float, seed: Optional[int] = None) -> np.ndarray:
    """
    Generate fGn using Cholesky decomposition of the covariance matrix.
    Slower O(n^3) but exact and reliable for moderate n.
    """
    if seed is not None:
        set_seed(seed)

    k = np.arange(n)
    # Covariance matrix
    # gamma(i, j) = gamma(|i-j|)
    dist = np.abs(k[:, None] - k[None, :])
    cov = 0.5 * (np.abs(dist + 1)**(2 * h) - 2 * np.abs(dist)**(2 * h) + np.abs(dist - 1)**(2 * h))

    # Ensure symmetry
    cov = (cov + cov.T) / 2
    # Add small jitter for numerical stability
    cov += 1e-10 * np.eye(n)

    try:
        L = np.linalg.cholesky(cov)
        z = np.random.randn(n)
        return L @ z
    except np.linalg.LinAlgError:
        # If Cholesky fails, add more jitter
        cov += 1e-6 * np.eye(n)
        L = np.linalg.cholesky(cov)
        z = np.random.randn(n)
        return L @ z


def generate_arfima(n: int, d: float, seed: Optional[int] = None) -> np.ndarray:
    """
    Generate ARFIMA(0, d, 0) process (fractional noise).
    This is equivalent to fGn with H = d + 0.5.
    """
    if seed is not None:
        set_seed(seed)

    h = d + 0.5
    if h <= 0 or h >= 1:
        raise ValueError("H = d + 0.5 must be in (0, 1).")

    return generate_fgn(n, h, seed)


def compute_theoretical_vif(h: float) -> float:
    """
    Compute the theoretical Variance Inflation Factor (VIF) for a given H.
    VIF approx = n^(2H) / n = n^(2H - 1) ?
    Actually, VIF = Var(mean) / (sigma^2 / n).
    For fGn, Var(mean) ~ n^(2H-2). So VIF ~ n^(2H-1).
    However, we usually define VIF as the factor by which variance is inflated
    relative to i.i.d. So VIF = n^(2H-1) is the scaling factor for the variance of the mean.
    But often VIF is reported as the ratio of the variance of the mean to the i.i.d. variance.
    Let's use the standard definition: VIF = n^(2H-1).
    Note: This depends on n. We return the exponent or a normalized value?
    The task asks for "theoretical VIF". Let's return the factor for a generic n=1000
    or return the formula value. Since VIF is n-dependent, we return the factor for n=1.
    Wait, VIF is typically defined as:
    VIF = 1 + 2 * sum_{k=1}^{n-1} (1 - k/n) * rho_k
    For large n and fGn, VIF ~ n^(2H-1).
    Let's return the asymptotic factor: n^(2H-1).
    But since n is not passed, we return the exponent (2H-1) or assume a standard n?
    The prompt says "compute theoretical VIF". Let's return the value for a standard n=1000
    or just the formula component.
    Actually, in the context of the study, we likely compare VIF across H.
    Let's return the factor for n=1000 as a representative, or better, the exponent.
    Let's implement the exact sum for a given n? No, n is not here.
    Let's return the asymptotic scaling factor: n^(2H-1).
    We will return the value for n=1000 to make it a scalar, but note it's n-dependent.
    Alternatively, return the exponent 2H-1.
    Let's return the exponent 2H-1, as it's the core theoretical metric.
    Re-reading: "compute theoretical VIF".
    Let's assume n=1000 for the calculation to provide a scalar value, as VIF is a scalar.
    """
    n_ref = 1000
    return n_ref ** (2 * h - 1)


def compute_n_eff(h: float, n: int) -> float:
    """
    Compute the effective sample size N_eff for a given H and n.
    N_eff = n / VIF
    """
    vif = n ** (2 * h - 1)
    return n / vif


def shuffle_series(series: Union[pd.Series, np.ndarray], seed: Optional[int] = None) -> Union[pd.Series, np.ndarray]:
    """
    Generate a shuffled (permuted) version of the series to create a null distribution.
    This destroys any temporal dependence (autocorrelation) while preserving the marginal distribution.

    Args:
        series: Input time series (pd.Series or np.ndarray).
        seed: Random seed for reproducibility.

    Returns:
        Shuffled series of the same type.
    """
    if seed is not None:
        set_seed(seed)

    if isinstance(series, pd.Series):
        # Shuffle the values, preserving the index
        values = series.values.copy()
        np.random.shuffle(values)
        return pd.Series(values, index=series.index, name=series.name)
    elif isinstance(series, np.ndarray):
        values = series.copy()
        np.random.shuffle(values)
        return values
    else:
        raise TypeError("Input must be a pandas Series or numpy array.")


def generate_null_distributions(
    series_list: List[Union[pd.Series, np.ndarray]],
    n_shuffles: int = 1000,
    seed: Optional[int] = None
) -> List[List[np.ndarray]]:
    """
    Generate null distributions by shuffling each series multiple times.

    Args:
        series_list: List of series (real or synthetic) to shuffle.
        n_shuffles: Number of shuffled versions to generate per series.
        seed: Random seed.

    Returns:
        List of lists, where each inner list contains the shuffled versions of the corresponding series.
    """
    if seed is not None:
        set_seed(seed)

    null_distributions = []
    for i, series in enumerate(series_list):
        logger.info(f"Generating {n_shuffles} shuffled versions for series {i+1}/{len(series_list)}")
        shuffles = []
        for j in range(n_shuffles):
            # Use a derived seed for each shuffle to ensure reproducibility
            derived_seed = seed + j if seed is not None else None
            shuffles.append(shuffle_series(series, seed=derived_seed))
        null_distributions.append(shuffles)

    return null_distributions
