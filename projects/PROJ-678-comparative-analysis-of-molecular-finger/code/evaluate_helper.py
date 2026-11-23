"""
Helper utilities for statistical evaluation used by the unit tests.

This module deliberately contains only lightweight, pure‑Python
functionality so that it can be imported without pulling in the full
``code.evaluate`` pipeline (which has many side‑effects such as file I/O).

The primary function implemented here is ``perform_corrected_resampled_ttest``,
which follows the Nadeau & Bengio (2003) correction for repeated
cross‑validation.
"""

from __future__ import annotations

import numpy as np
from scipy.stats import t


def perform_corrected_resampled_ttest(
    *,
    scores_a: list[float] | np.ndarray,
    scores_b: list[float] | np.ndarray,
    n_folds: int,
    random_state: int | None = 42,
) -> float:
    """
    Compute the corrected resampled t‑test (Nadeau & Bengio, 2003).

    Parameters
    ----------
    scores_a, scores_b:
        Lists or arrays containing the performance metric (e.g. ROC‑AUC)
        for each fold of the two compared models. The length must equal
        ``n_folds``.
    n_folds:
        Number of cross‑validation folds used to generate the scores.
    random_state:
        Seed for reproducibility – currently unused but kept for API
        compatibility with potential extensions.

    Returns
    -------
    float
        Two‑sided p‑value for the null hypothesis that the mean
        performance of the two models is equal.

    Notes
    -----
    The correction accounts for the fact that the same data points are
    used in multiple training folds, which inflates the variance of the
    naïve paired t‑test.  The variance correction factor is:

        var_corrected = (1 / n_folds + 1 / (n_folds * (n_folds - 1))) * s²

    where ``s²`` is the unbiased sample variance of the per‑fold
    differences.
    """
    # Convert inputs to NumPy arrays for vectorised operations.
    a = np.asarray(scores_a, dtype=float)
    b = np.asarray(scores_b, dtype=float)

    if a.shape != b.shape:
        raise ValueError("scores_a and scores_b must have the same shape")
    if a.size != n_folds:
        raise ValueError(
            f"The number of provided scores ({a.size}) does not match n_folds ({n_folds})"
        )

    # Per‑fold differences.
    diffs = a - b
    mean_diff = diffs.mean()
    # Unbiased variance (ddof=1).
    var = diffs.var(ddof=1)

    # Nadeau & Bengio variance correction.
    var_corrected = (1.0 / n_folds + 1.0 / (n_folds * (n_folds - 1))) * var

    # t‑statistic.
    t_stat = mean_diff / np.sqrt(var_corrected)

    # Two‑tailed p‑value with df = n_folds - 1.
    p_value = 2.0 * (1.0 - t.cdf(np.abs(t_stat), df=n_folds - 1))

    # Guard against numerical issues that could push p slightly outside [0, 1].
    p_value = max(0.0, min(1.0, p_value))

    return p_value
