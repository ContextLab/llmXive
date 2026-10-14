"""entropy.py
-----------------
Compute multiscale sample entropy (mSE) for fMRI parcel time series.

The main public function is ``multiscale_entropy`` which accepts a
``pandas.DataFrame`` where rows correspond to time points and columns
correspond to parcels (e.g. ``parcel_0`` … ``parcel_399``).  For each
parcel the function performs the following steps:

1.  For each scale factor ``s`` in ``scales`` a coarse‑grained series is
    created by averaging non‑overlapping windows of length ``s``.
2.  The sample entropy of the coarse‑grained series is computed using
    :func:`pyentropy.sample_entropy` with embedding dimension ``m`` and
    tolerance ``r``.
3.  The entropy values across the requested scales are averaged to obtain
    a single scalar per parcel.

Parcels that become too short after coarse‑graining (i.e. length <
``m + 1``) are considered invalid.  Their IDs are written to
``data/derived/invalid_parcels.csv`` and their resulting entropy is set
to ``np.nan``.

The function returns a ``pandas.Series`` indexed by parcel name.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from pyentropy import sample_entropy
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

def _coarse_grain(series: np.ndarray, scale: int) -> np.ndarray:
    """Return a coarse‑grained version of ``series`` at the given ``scale``.

    The series is reshaped to (n_windows, scale) and averaged along the
    second axis.  Any leftover points that do not fit into a full window
    are discarded (standard practice for multiscale entropy).
    """
    if scale <= 1:
        return series
    n_points = len(series)
    n_windows = n_points // scale
    if n_windows == 0:
        return np.array([])  # will be flagged as invalid later
    trimmed = series[: n_windows * scale]
    reshaped = trimmed.reshape((n_windows, scale))
    return reshaped.mean(axis=1)

def multiscale_entropy(
    ts: pd.DataFrame,
    scales: tuple[int, ...] = (1, 2, 3, 4, 5),
    m: int = 2,
    r: float = 0.15,
) -> pd.Series:
    """Compute multiscale sample entropy for each parcel.

    Parameters
    ----------
    ts : pandas.DataFrame
        Time‑point × parcel matrix. Columns are parcel identifiers.
    scales : tuple[int, ...], optional
        Scale factors to use (default: 1‑5).
    m : int, optional
        Embedding dimension for sample entropy (default: 2).
    r : float, optional
        Tolerance (fraction of standard deviation) for sample entropy
        (default: 0.15).

    Returns
    -------
    pandas.Series
        Entropy values indexed by parcel name. Invalid parcels have
        ``np.nan``.
    """
    if not isinstance(ts, pd.DataFrame):
        raise TypeError("ts must be a pandas DataFrame")

    invalid_parcels: list[str] = []
    entropy_results: dict[str, float] = {}

    for parcel in ts.columns:
        series = ts[parcel].to_numpy(dtype=float)

        per_scale_entropy: list[float] = []
        for scale in scales:
            cg_series = _coarse_grain(series, scale)

            # Need at least (m + 1) points to compute sample entropy
            if len(cg_series) < m + 1:
                # Mark as invalid for this parcel and break out of the scale loop
                per_scale_entropy = []
                break

            # pyentropy expects the tolerance as an absolute value; the common
            # practice is to multiply ``r`` by the standard deviation of the
            # series.
            tolerance = r * np.std(cg_series, ddof=0)
            try:
                se = sample_entropy(cg_series, m=m, r=tolerance)
                per_scale_entropy.append(se)
            except Exception as exc:
                log.error(
                    "Sample entropy failed for parcel %s at scale %s: %s",
                    parcel,
                    scale,
                    exc,
                )
                per_scale_entropy = []
                break

        if not per_scale_entropy:
            # Parcel could not be processed (insufficient points or error)
            entropy_results[parcel] = np.nan
            invalid_parcels.append(parcel)
        else:
            entropy_results[parcel] = float(np.mean(per_scale_entropy))

    # Write invalid parcel IDs to the prescribed location
    if invalid_parcels:
        invalid_path = paths.data("derived", "invalid_parcels.csv")
        pd.Series(invalid_parcels, name="parcel_id").to_csv(
            invalid_path, index=False
        )
        log.info("Invalid parcels written to %s", invalid_path)

    return pd.Series(entropy_results, name="entropy")
