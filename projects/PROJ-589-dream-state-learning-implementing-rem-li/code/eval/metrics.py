"""
Evaluation metrics utilities.

Currently provides a thin wrapper around SciPy's Wilcoxon signed‑rank test
for comparing two sets of accuracy scores (or any other paired metric).
The wrapper validates input lengths and returns a dictionary with the
test statistic and p‑value, making it easy to serialize or log.
"""

from typing import List, Dict, Literal

import numpy as np
from scipy.stats import wilcoxon


def wilcoxon_test(
    accuracies_a: List[float],
    accuracies_b: List[float],
    *,
    alternative: Literal["two-sided", "greater", "less"] = "two-sided",
) -> Dict[str, float]:
    """
    Compute the Wilcoxon signed‑rank test for two paired samples.

    Parameters
    ----------
    accuracies_a, accuracies_b: List[float]
        Paired accuracy (or metric) values from two experimental conditions.
    alternative: {"two-sided", "greater", "less"}, optional
        Defines the alternative hypothesis.  Defaults to ``"two-sided"``.

    Returns
    -------
    dict
        ``{"statistic": float, "p_value": float}`` containing the test
        statistic and the associated p‑value.

    Raises
    ------
    ValueError
        If the input sequences are of different lengths or contain fewer
        than two non‑zero differences (the requirement of SciPy's
        ``wilcoxon`` implementation).
    """
    if len(accuracies_a) != len(accuracies_b):
        raise ValueError("Input sequences must have the same length.")

    # Convert to NumPy arrays for safety; SciPy will handle NaNs appropriately.
    a_arr = np.asarray(accuracies_a, dtype=float)
    b_arr = np.asarray(accuracies_b, dtype=float)

    # SciPy's wilcoxon raises a ValueError if the number of non‑zero
    # differences is less than 2; we propagate that error.
    stat, p_value = wilcoxon(a_arr, b_arr, alternative=alternative)

    return {"statistic": float(stat), "p_value": float(p_value)}
