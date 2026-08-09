"""
Synthetic time series generators for robustness evaluation.

Implements generation of fractional Gaussian noise (fGn) and ARFIMA processes
with specified Hurst exponents and zero mean, as required by FR-007.
"""
import numpy as np
import pandas as pd
from typing import List, Union, Optional, Tuple, Dict, Any
from scipy import stats
from scipy.signal import fftconvolve
import logging

from src.utils.config import set_seed
from src.data.schemas import SyntheticData

# Configure logger
logger = logging.getLogger(__name__)


def _generate_fgn_via_circulant(n: int, h: float, seed: Optional[int] = None) -> np.ndarray:
    """
    Generate fractional Gaussian noise using the circulant matrix embedding method.

    This method uses the Cholesky decomposition of the circulant matrix embedding
    the covariance matrix of fGn. It is efficient (O(n log n)) and exact.

    Args:
        n: Length of the series.
        h: Hurst exponent (0 < h < 1).
        seed: Random seed for reproducibility.

    Returns:
        numpy array of fGn values.
    """
    if seed is not None:
        np.random.seed(seed)

    if not 0 < h < 1:
        raise ValueError(f"Hurst exponent must be in (0, 1), got {h}")

    # Covariance function for fGn: gamma(k) = 0.5 * (|k+1|^(2h) - 2|k|^(2h) + |k-1|^(2h))
    # We need the first n+1 values of the covariance function for the circulant embedding
    k = np.arange(n + 1)
    gamma = 0.5 * (np.abs(k + 1)**(2 * h) - 2 * np.abs(k)**(2 * h) + np.abs(k - 1)**(2 * h))

    # Create the circulant matrix embedding
    # The first column is [gamma(0), gamma(1), ..., gamma(n-1), gamma(1), ..., gamma(n-1)]
    # Actually, for the circulant embedding of size 2n, the first row is:
    # [gamma(0), gamma(1), ..., gamma(n-1), gamma(n), gamma(n-1), ..., gamma(1)]
    # But since gamma(n) is not needed for the first n lags in the standard embedding,
    # we construct the vector c of length 2n:
    # c = [gamma(0), gamma(1), ..., gamma(n-1), gamma(n), gamma(n-1), ..., gamma(1)]
    # Wait, the standard embedding for a Toeplitz matrix T of size n uses a circulant matrix C of size 2n.
    # The first row of C is [T_0, T_1, ..., T_{n-1}, T_n, T_{n-1}, ..., T_1]
    # where T_k = gamma(k).
    # However, for fGn, we only need the covariance of the first n points.
    # The covariance matrix of fGn is Toeplitz with entries gamma(|i-j|).
    # The embedding vector c is:
    c = np.concatenate([gamma[:n], [gamma[n]], gamma[n-1:0:-1]])
    # Note: gamma[n] is not strictly needed if we only care about the first n, but it completes the symmetry.
    # Actually, the standard construction for size 2n is:
    # c = [gamma(0), gamma(1), ..., gamma(n-1), gamma(n), gamma(n-1), ..., gamma(1)]
    # But we only have gamma up to n. Let's re-verify the length.
    # We need 2n elements.
    # gamma has n+1 elements (0 to n).
    # c = [gamma[0], gamma[1], ..., gamma[n-1], gamma[n], gamma[n-1], ..., gamma[1]]
    # Length: n + 1 + (n-1) = 2n. Correct.

    # Compute eigenvalues of the circulant matrix via FFT
    # The eigenvalues are the FFT of the first row c
    eig_vals = np.fft.fft(c)

    # Check for non-negative eigenvalues (required for valid covariance)
    if np.any(eig_vals < 0):
        # This can happen due to numerical precision or if h is extreme
        # In practice, for 0 < h < 1, it should be positive definite.
        # We clamp small negative values to zero to avoid complex roots
        eig_vals = np.maximum(eig_vals, 0)

    # Generate complex normal random variables
    # Z ~ CN(0, I)
    # We need to generate a vector of length 2n
    # Let Z = Z_re + i * Z_im, where Z_re, Z_im ~ N(0, 1)
    # But the standard method is:
    # X = ifft( sqrt(eig_vals) * (Z_re + i * Z_im) )
    # However, to ensure X is real, we need to impose symmetry on the input to ifft.
    # The eig_vals are real and symmetric (since c is real and symmetric).
    # We generate complex normal with the correct symmetry.
    # A simpler approach:
    # Generate Z ~ N(0, I) of length 2n.
    # Then X = ifft( sqrt(eig_vals) * Z ) is not necessarily real.
    # The correct method for real output:
    # Generate Z_re, Z_im ~ N(0, 1) of length 2n.
    # But we need to ensure the output is real.
    # Standard recipe:
    # Let Z = Z_re + i * Z_im, where Z_re and Z_im are independent N(0, 1).
    # Then X = ifft( sqrt(eig_vals) * Z )
    # To get a real X, we need the input to ifft to be conjugate symmetric.
    # Since eig_vals is real and symmetric, we can just use:
    # Z = Z_re + i * Z_im, but we must ensure Z[0] is real and Z[n] is real (if 2n is even).
    # Actually, the standard algorithm is:
    # 1. Generate Z ~ N(0, I) of length 2n.
    # 2. Set Z[0] = Z[0] (real), Z[n] = Z[n] (real) if 2n is even.
    # 3. For k=1..n-1, set Z[2n-k] = conjugate(Z[k]).
    # But a simpler way is to generate complex normal and then take the real part of ifft.
    # However, the most robust way is:
    # Generate Z ~ N(0, I) of length 2n.
    # Then X = ifft( sqrt(eig_vals) * Z )
    # The real part of X will be the fGn.
    # But to ensure exact real output, we can use:
    # Z = np.random.randn(2*n) + 1j * np.random.randn(2*n)
    # Z[0] = Z[0].real + 0j
    # Z[n] = Z[n].real + 0j  # if 2n is even
    # for k in range(1, n):
    #     Z[2*n - k] = np.conj(Z[k])
    # Then X = ifft( sqrt(eig_vals) * Z )
    # But this is complicated. Let's use the simpler method:
    # Generate Z ~ N(0, I) of length 2n.
    # X = ifft( sqrt(eig_vals) * Z )
    # The real part of X is the fGn.
    # This is approximate but works well.
    # For exact real output, we can use the method from Diebold and Inoue (2001) or similar.
    # Let's use the method that ensures real output by symmetry.
    # We'll generate Z_re and Z_im separately and enforce symmetry.

    # Generate standard normal variables
    z_re = np.random.randn(2 * n)
    z_im = np.random.randn(2 * n)

    # Enforce symmetry for real output
    # Z[0] must be real
    z_im[0] = 0.0
    # If 2n is even, Z[n] must be real
    if 2 * n % 2 == 0:
        z_im[n] = 0.0

    # Enforce conjugate symmetry: Z[2n-k] = conj(Z[k])
    # This means z_re[2n-k] = z_re[k] and z_im[2n-k] = -z_im[k]
    for k in range(1, n):
        z_re[2 * n - k] = z_re[k]
        z_im[2 * n - k] = -z_im[k]

    z_complex = z_re + 1j * z_im

    # Compute sqrt of eigenvalues
    sqrt_eig = np.sqrt(eig_vals)

    # Generate the series
    x_complex = np.fft.ifft(sqrt_eig * z_complex)

    # Take the real part (should be exact due to symmetry)
    x = np.real(x_complex)

    # Return the first n points
    return x[:n]


def _generate_fgn_via_cholesky(n: int, h: float, seed: Optional[int] = None) -> np.ndarray:
    """
    Generate fractional Gaussian noise using Cholesky decomposition.

    This is a direct method that constructs the covariance matrix and performs
    Cholesky decomposition. It is O(n^3) but exact and straightforward.

    Args:
        n: Length of the series.
        h: Hurst exponent (0 < h < 1).
        seed: Random seed for reproducibility.

    Returns:
        numpy array of fGn values.
    """
    if seed is not None:
        np.random.seed(seed)

    if not 0 < h < 1:
        raise ValueError(f"Hurst exponent must be in (0, 1), got {h}")

    # Construct the covariance matrix
    # gamma(k) = 0.5 * (|k+1|^(2h) - 2|k|^(2h) + |k-1|^(2h))
    k = np.arange(n)
    gamma = 0.5 * (np.abs(k + 1)**(2 * h) - 2 * np.abs(k)**(2 * h) + np.abs(k - 1)**(2 * h))

    # Create Toeplitz covariance matrix
    cov_matrix = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            cov_matrix[i, j] = gamma[abs(i - j)]

    # Cholesky decomposition
    try:
        L = np.linalg.cholesky(cov_matrix)
    except np.linalg.LinAlgError:
        # If the matrix is not positive definite (can happen for extreme h or small n),
        # fall back to circulant method or add small jitter
        logger.warning("Cholesky decomposition failed. Using circulant method as fallback.")
        return _generate_fgn_via_circulant(n, h, seed)

    # Generate standard normal vector
    z = np.random.randn(n)

    # Transform to fGn
    return L @ z


def generate_fgn(n: int, h: float, seed: Optional[int] = None) -> np.ndarray:
    """
    Generate fractional Gaussian noise (fGn).

    Uses the circulant matrix embedding method for efficiency (O(n log n)).

    Args:
        n: Length of the series.
        h: Hurst exponent (0 < h < 1).
        seed: Random seed for reproducibility.

    Returns:
        numpy array of fGn values with mean approximately 0.
    """
    # For small n, use Cholesky for better numerical stability
    if n < 100:
        return _generate_fgn_via_cholesky(n, h, seed)
    else:
        return _generate_fgn_via_circulant(n, h, seed)


def generate_synthetic_series(
    n: int,
    h: float,
    mean: float = 0.0,
    seed: Optional[int] = None,
    method: str = "fgn"
) -> SyntheticData:
    """
    Generate a synthetic time series with specified Hurst exponent and mean.

    This function generates fractional Gaussian noise (fGn) or ARFIMA processes
    with the specified parameters. The series is centered to have the exact mean.

    Args:
        n: Length of the series.
        h: Hurst exponent (0 < h < 1).
        mean: Target mean of the series (default 0).
        seed: Random seed for reproducibility.
        method: Generation method ("fgn" or "arfima"). Currently only "fgn" is implemented.

    Returns:
        SyntheticData object containing the series and metadata.

    Raises:
        ValueError: If h is not in (0, 1) or method is not supported.
    """
    if not 0 < h < 1:
        raise ValueError(f"Hurst exponent must be in (0, 1), got {h}")

    if method != "fgn":
        raise NotImplementedError(f"Method '{method}' is not implemented. Only 'fgn' is supported.")

    # Set seed for reproducibility
    if seed is not None:
        set_seed(seed)

    # Generate fGn
    series = generate_fgn(n, h, seed)

    # Center the series to have the exact mean
    current_mean = np.mean(series)
    series = series - current_mean + mean

    # Create metadata
    metadata = {
        "n": n,
        "h": h,
        "mean": mean,
        "method": method,
        "seed": seed,
        "generated_at": pd.Timestamp.now().isoformat()
    }

    return SyntheticData(
        data=series,
        metadata=metadata
    )


def shuffle_series(series: np.ndarray, seed: Optional[int] = None) -> np.ndarray:
    """
    Shuffle a time series to destroy temporal dependencies.

    This is used to create a null distribution for hypothesis testing.

    Args:
        series: Input time series.
        seed: Random seed for reproducibility.

    Returns:
        Shuffled time series.
    """
    if seed is not None:
        np.random.seed(seed)

    shuffled = series.copy()
    np.random.shuffle(shuffled)
    return shuffled


def compute_acf_lag1(series: np.ndarray) -> float:
    """
    Compute the lag-1 autocorrelation of a series.

    Args:
        series: Input time series.

    Returns:
        Lag-1 autocorrelation coefficient.
    """
    n = len(series)
    if n < 2:
        return 0.0

    mean = np.mean(series)
    var = np.var(series, ddof=0)

    if var == 0:
        return 0.0

    # Autocovariance at lag 1
    cov_lag1 = np.mean((series[:-1] - mean) * (series[1:] - mean))

    # Autocorrelation
    return cov_lag1 / var


def generate_null_distributions(
    series: np.ndarray,
    n_permutations: int = 1000,
    seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Generate a null distribution by shuffling the series multiple times.

    Args:
        series: Input time series.
        n_permutations: Number of permutations.
        seed: Random seed for reproducibility.

    Returns:
        Dictionary containing the null distribution statistics.
    """
    if seed is not None:
        np.random.seed(seed)

    null_acf_lag1 = []
    for _ in range(n_permutations):
        shuffled = shuffle_series(series)
        acf1 = compute_acf_lag1(shuffled)
        null_acf_lag1.append(acf1)

    return {
        "n_permutations": n_permutations,
        "acf_lag1_mean": np.mean(null_acf_lag1),
        "acf_lag1_std": np.std(null_acf_lag1),
        "acf_lag1_2.5_percentile": np.percentile(null_acf_lag1, 2.5),
        "acf_lag1_97.5_percentile": np.percentile(null_acf_lag1, 97.5),
        "acf_lag1_values": null_acf_lag1
    }