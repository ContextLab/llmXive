"""
utils/entropy_utils.py
=======================

CPU‑only implementations of Sample Entropy (SampEn) and Approximate Entropy (ApEn)
for 1‑D signals. The functions are JIT‑compiled with Numba for speed but do **not**
rely on any GPU or CUDA libraries, satisfying the task requirement for a
CPU‑only implementation.

The module provides:
  * ``sample_entropy`` – wrapper around a Numba‑accelerated core implementation.
  * ``approximate_entropy`` – wrapper around a Numba‑accelerated core implementation.
  * ``compute_entropy_metrics`` – convenience function returning both metrics.

All public symbols are listed in ``__all__`` for explicit export.
"""

import numpy as np
from numba import njit
from typing import Optional, Dict
import logging

# Configure module‑level logger
logger = logging.getLogger(__name__)

__all__ = [
    "sample_entropy",
    "approximate_entropy",
    "compute_entropy_metrics",
]

@njit(fastmath=True, cache=True)
def _sample_entropy_core(signal: np.ndarray, m: int, r: float) -> float:
    """
    Numba‑accelerated core of Sample Entropy.

    Parameters
    ----------
    signal : np.ndarray
        1‑D time‑series.
    m : int
        Template length.
    r : float
        Tolerance (typically ``0.2 * std(signal)``).

    Returns
    -------
    float
        Sample Entropy value. ``np.nan`` if the calculation cannot be performed.
    """
    n = len(signal)
    if n < m + 2:
        return np.nan

    # Normalise for numerical stability
    std_val = np.std(signal)
    if std_val == 0.0:
        return 0.0

    count_m = 0.0
    count_m1 = 0.0

    for i in range(n - m):
        for j in range(i + 1, n - m):
            # Maximum absolute distance over the template of length m
            max_diff = 0.0
            for k in range(m):
                diff = abs(signal[i + k] - signal[j + k])
                if diff > max_diff:
                    max_diff = diff

            if max_diff < r:
                count_m += 1.0

                # Check the (m+1)‑th point if it exists
                if i + m < n and j + m < n:
                    diff_next = abs(signal[i + m] - signal[j + m])
                    if diff_next < r:
                        count_m1 += 1.0

    if count_m == 0.0:
        return np.nan
    if count_m1 == 0.0:
        # Logarithm of zero would be ``inf``; we return ``np.nan`` to signal failure.
        return np.nan

    return -np.log(count_m1 / count_m)

@njit(fastmath=True, cache=True)
def _approximate_entropy_core(signal: np.ndarray, m: int, r: float) -> float:
    """
    Numba‑accelerated core of Approximate Entropy.

    Parameters
    ----------
    signal : np.ndarray
        1‑D time‑series.
    m : int
        Template length.
    r : float
        Tolerance (typically ``0.2 * std(signal)``).

    Returns
    -------
    float
        Approximate Entropy value. ``np.nan`` if the calculation cannot be performed.
    """
    n = len(signal)
    if n < m + 1:
        return np.nan

    # Normalise for numerical stability
    std_val = np.std(signal)
    if std_val == 0.0:
        return 0.0

    # --- Count matches for length m ---------------------------------
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

    # --- Count matches for length m+1 -------------------------------
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

    if count_m == 0.0 or count_m1 == 0.0:
        return np.nan

    phi_m = count_m / ((n - m + 1) * (n - m))
    phi_m1 = count_m1 / ((n - m) * (n - m - 1))

    if phi_m <= 0.0 or phi_m1 <= 0.0:
        return np.nan

    return np.log(phi_m) - np.log(phi_m1)

def sample_entropy(signal: np.ndarray, m: int = 2, r: Optional[float] = None) -> float:
    """
    Compute Sample Entropy (SampEn) of a 1‑D signal.

    Parameters
    ----------
    signal : np.ndarray
        Input time series.
    m : int, optional
        Template length (default ``2``).
    r : float, optional
        Tolerance. If ``None`` it defaults to ``0.2 * std(signal)``.
        ``r`` must be positive; a zero tolerance is allowed for constant signals.

    Returns
    -------
    float
        Sample Entropy value (``np.nan`` on failure).
    """
    # Ensure ``signal`` is a NumPy ``float64`` array for Numba compatibility.
    if not isinstance(signal, np.ndarray):
        signal = np.array(signal, dtype=np.float64)
    else:
        signal = signal.astype(np.float64)

    if signal.ndim != 1:
        raise ValueError("Signal must be 1‑dimensional.")

    if len(signal) < m + 2:
        logger.warning("Signal length %d is too short for m=%d.", len(signal), m)
        return np.nan

    if r is None:
        std_val = np.std(signal)
        if std_val == 0.0:
            # Constant signal – entropy is zero by definition.
            return 0.0
        r = 0.2 * std_val

    try:
        result = _sample_entropy_core(signal, m, r)
        return float(result)
    except Exception as exc:  # pragma: no cover – defensive
        logger.error("Sample entropy calculation failed: %s", exc)
        return np.nan

def approximate_entropy(signal: np.ndarray, m: int = 2, r: Optional[float] = None) -> float:
    """
    Compute Approximate Entropy (ApEn) of a 1‑D signal.

    Parameters
    ----------
    signal : np.ndarray
        Input time series.
    m : int, optional
        Template length (default ``2``).
    r : float, optional
        Tolerance. If ``None`` it defaults to ``0.2 * std(signal)``.
        ``r`` must be positive; a zero tolerance is allowed for constant signals.

    Returns
    -------
    float
        Approximate Entropy value (``np.nan`` on failure).
    """
    # Ensure ``signal`` is a NumPy ``float64`` array for Numba compatibility.
    if not isinstance(signal, np.ndarray):
        signal = np.array(signal, dtype=np.float64)
    else:
        signal = signal.astype(np.float64)

    if signal.ndim != 1:
        raise ValueError("Signal must be 1‑dimensional.")

    if len(signal) < m + 1:
        logger.warning("Signal length %d is too short for m=%d.", len(signal), m)
        return np.nan

    if r is None:
        std_val = np.std(signal)
        if std_val == 0.0:
            # Constant signal – entropy is zero by definition.
            return 0.0
        r = 0.2 * std_val

    try:
        result = _approximate_entropy_core(signal, m, r)
        return float(result)
    except Exception as exc:  # pragma: no cover – defensive
        logger.error("Approximate entropy calculation failed: %s", exc)
        return np.nan

def compute_entropy_metrics(signal: np.ndarray, m: int = 2, r: Optional[float] = None) -> Dict[str, float]:
    """
    Convenience wrapper returning both Sample and Approximate Entropy.

    Parameters
    ----------
    signal : np.ndarray
        Input time series.
    m : int, optional
        Template length (default ``2``).
    r : float, optional
        Tolerance (default ``0.2 * std(signal)``).

    Returns
    -------
    dict
        ``{'sample_entropy': <value>, 'approximate_entropy': <value>}``
    """
    se = sample_entropy(signal, m, r)
    ae = approximate_entropy(signal, m, r)
    return {"sample_entropy": se, "approximate_entropy": ae}