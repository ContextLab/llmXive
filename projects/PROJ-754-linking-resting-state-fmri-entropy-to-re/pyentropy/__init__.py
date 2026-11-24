"""
Minimal stub of the ``pyentropy`` package providing a ``sample_entropy``
implementation compatible with the project's needs.

The algorithm follows the standard definition of sample entropy:
For a time series ``x`` of length ``N``, embedding dimension ``m`` and
tolerance ``r``, sample entropy is:

    -ln( A / B )

where ``B`` is the number of matching template pairs of length ``m`` and
``A`` is the number of matching pairs of length ``m+1``.

This implementation is deliberately simple but fully deterministic and
works on real numeric data without external dependencies.
"""
import numpy as np

def _embed(series: np.ndarray, m: int) -> np.ndarray:
    """
    Create a matrix where each row is a length‑``m`` embedding of the series.
    """
    N = len(series)
    if N < m:
        return np.empty((0, m))
    return np.lib.stride_tricks.sliding_window_view(series, window_shape=m)

def sample_entropy(series: np.ndarray, m: int = 2, r: float = 0.2) -> float:
    """
    Compute sample entropy of ``series`` using embedding dimension ``m`` and
    tolerance ``r`` (absolute value, not a fraction).

    Parameters
    ----------
    series : np.ndarray
        1‑D array of time‑series values.
    m : int, optional
        Embedding dimension (default 2).
    r : float, optional
        Tolerance (absolute).  Typical practice is ``r`` = 0.2 *
        ``np.std(series)``; callers are responsible for scaling.

    Returns
    -------
    float
        Sample entropy.  Returns ``np.inf`` if no matches are found
        (consistent with the mathematical definition).
    """
    series = np.asarray(series, dtype=float)
    if series.ndim != 1:
        raise ValueError("sample_entropy expects a 1‑D array")

    N = len(series)
    if N <= m + 1:
        return np.inf

    # Embed the series for dimensions m and m+1
    emb_m = _embed(series, m)
    emb_m1 = _embed(series, m + 1)

    # Pairwise Chebyshev distances
    def _count_matches(emb):
        # Compute the maximum absolute difference across each dimension
        diff = np.abs(emb[:, None, :] - emb[None, :, :])
        max_diff = diff.max(axis=2)
        # Count pairs (i < j) where distance <= r
        return np.sum((max_diff <= r) & (np.arange(len(emb))[:, None] < np.arange(len(emb))[None, :]))

    B = _count_matches(emb_m)
    A = _count_matches(emb_m1)

    if B == 0:
        return np.inf
    if A == 0:
        return np.inf

    return -np.log(A / B)
