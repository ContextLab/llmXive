"""CPU-only Sample Entropy (SampEn) and Approximate Entropy (ApEn).

Implements the standard algorithms (Pincus 1991; Richman & Moorman 2000)
using NumPy/SciPy only — no CUDA, no GPU dependencies.

Parameters follow the project convention: m = 2, r = 0.2 * std(signal).
All computations use float64 precision for numerical stability.
"""
from __future__ import annotations

import numpy as np
from scipy.spatial.distance import cdist


def _prepare(signal, m: int, r: float):
    """Validate inputs and return templates as float64 arrays."""
    x = np.asarray(signal, dtype=np.float64).ravel()
    if x.size < m + 2:
        raise ValueError(
            f"Signal too short ({x.size} samples) for m={m}; "
            "need at least m+2 samples."
        )
    if not np.isfinite(x).all():
        raise ValueError("Signal contains NaN or Inf values.")
    if r is None or not np.isfinite(r) or r < 0:
        raise ValueError(f"Invalid tolerance r: {r!r}")
    return x


def _template_counts(x: np.ndarray, m: int, r: float) -> float:
    """Count matching template pairs (i != j) within Chebyshev distance r."""
    n = x.size
    # Build all embedded vectors of length m
    n_templates = n - m + 1
    templates = np.empty((n_templates, m), dtype=np.float64)
    for i in range(m):
        templates[:, i] = x[i:i + n_templates]
    # Pairwise Chebyshev distances (vectorized, CPU-only)
    dists = cdist(templates, templates, metric="chebyshev")
    # Exclude self-matches on the diagonal
    np.fill_diagonal(dists, np.inf)
    matches = np.count_nonzero(dists <= r)
    return float(matches)


def sample_entropy(signal, m: int = 2, r: float = 0.2) -> float:
    """Sample Entropy (SampEn).

    SampEn = -log(A / B) where B is the number of matching m-length
    template pairs and A the number of matching (m+1)-length pairs.

    Parameters
    ----------
    signal : array-like
        1-D time series.
    m : int
        Embedding dimension (project default 2).
    r : float
        Tolerance (project default 0.2 * std of the signal).

    Returns
    -------
    float
        SampEn value; 0.0 when no matches are found (degenerate case,
        e.g. constant signals), never NaN or Inf.
    """
    x = _prepare(signal, m, r)
    b = _template_counts(x, m, r)
    a = _template_counts(x, m + 1, r)
    if b == 0 or a == 0:
        # Degenerate case (e.g., constant signal or r too small):
        # define entropy as 0 rather than returning inf/NaN.
        return 0.0
    ratio = a / b
    if ratio <= 0:
        return 0.0
    return float(-np.log(ratio))


def approximate_entropy(signal, m: int = 2, r: float = 0.2) -> float:
    """Approximate Entropy (ApEn, Pincus 1991).

    ApEn = Phi_m - Phi_{m+1}, where Phi_k is the average natural-log
    conditional probability of k-length template matches (self-matches
    included, per the original definition).

    Parameters
    ----------
    signal : array-like
        1-D time series.
    m : int
        Embedding dimension (project default 2).
    r : float
        Tolerance (project default 0.2 * std of the signal).

    Returns
    -------
    float
        ApEn value; 0.0 in degenerate cases, never NaN or Inf.
    """
    x = _prepare(signal, m, r)

    def phi(k: int) -> float:
        n_templates = x.size - k + 1
        templates = np.empty((n_templates, k), dtype=np.float64)
        for i in range(k):
            templates[:, i] = x[i:i + n_templates]
        dists = cdist(templates, templates, metric="chebyshev")
        # ApEn includes self-matches (diagonal distance 0 <= r)
        counts = np.count_nonzero(dists <= r, axis=1).astype(np.float64)
        # counts is always >= 1 (self-match), so log is safe
        return float(np.mean(np.log(counts / n_templates)))

    value = phi(m) - phi(m + 1)
    if not np.isfinite(value):
        return 0.0
    return float(max(value, 0.0))


def compute_entropy_metrics(signal, m: int = 2, r_scale: float = 0.2) -> dict:
    """Compute both entropy metrics with the project-standard parameters.

    Uses r = r_scale * std(signal); for constant signals (std == 0) a
    small positive fallback tolerance is used so the result is 0.0
    rather than an error.
    """
    x = np.asarray(signal, dtype=np.float64).ravel()
    std = float(np.std(x))
    r = r_scale * std if std > 0 else 1e-10
    return {
        "SampEn": sample_entropy(x, m=m, r=r),
        "ApEn": approximate_entropy(x, m=m, r=r),
    }
