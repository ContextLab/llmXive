"""
Statistical tests utilities for the molecular dipole moment prediction project.
Currently provides a paired t-test implementation used to compare performance
metrics (e.g., RMSE) across different models or seeds.
"""

from __future__ import annotations

from typing import Sequence, Dict

import numpy as np
from scipy import stats


def paired_t_test(sample1: Sequence[float], sample2: Sequence[float]) -> Dict[str, float]:
    """
    Perform a paired two‑sample t‑test (dependent samples).

    Parameters
    ----------
    sample1, sample2 : Sequence[float]
        Numeric sequences of equal length representing paired observations.

    Returns
    -------
    dict
        Dictionary with keys:
        - ``t_stat``: t statistic value
        - ``p_value``: two‑tailed p‑value
        - ``df``: degrees of freedom (len(sample) - 1)

    Raises
    ------
    ValueError
        If the input sequences are of different lengths or have length < 2.
    """
    arr1 = np.asarray(sample1, dtype=float)
    arr2 = np.asarray(sample2, dtype=float)

    if arr1.shape != arr2.shape:
        raise ValueError("Input samples must have the same shape.")
    if arr1.size < 2:
        raise ValueError("At least two paired observations are required.")

    t_stat, p_value = stats.ttest_rel(arr1, arr2)
    df = arr1.size - 1

    return {"t_stat": float(t_stat), "p_value": float(p_value), "df": float(df)}
