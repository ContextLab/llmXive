"""
Utility functions for computing effect size metrics such as Cohen's d.

This module provides a robust implementation of Cohen's d that computes the
pooled standard deviation from the two groups defined by a binary outcome
variable. It is deliberately lightweight and has no side‑effects, making it
safe to import from any part of the pipeline.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from typing import Any


def compute_cohens_d(
    df: pd.DataFrame,
    outcome_col: str,
    feature_col: str,
    *,
    positive_group: Any | None = None,
    negative_group: Any | None = None,
) -> float:
    """
    Compute Cohen's d for a numeric feature between two groups defined by an
    outcome column.

    Parameters
    ----------
    df : pd.DataFrame
        The DataFrame containing the data.
    outcome_col : str
        Column name that encodes the binary outcome / group label.
    feature_col : str
        Column name of the numeric feature for which the effect size is
        calculated.
    positive_group : Any, optional
        Value in ``outcome_col`` that should be treated as the positive
        (first) group. If not supplied the first unique value encountered
        will be used.
    negative_group : Any, optional
        Value in ``outcome_col`` that should be treated as the negative
        (second) group. If not supplied the second unique value encountered
        will be used.

    Returns
    -------
    float
        Cohen's d, defined as (mean_pos - mean_neg) / pooled_std.

    Notes
    -----
    * The pooled standard deviation is calculated using the unbiased
      (n‑1) estimator for each group:
        
        s_pooled = sqrt( ((n1‑1)*s1² + (n2‑1)*s2²) / (n1 + n2 ‑ 2) )
    
    * The function raises ``ValueError`` if the outcome column does not
      contain exactly two distinct groups.
    """
    # Extract the two groups
    unique_vals = df[outcome_col].dropna().unique()
    if len(unique_vals) != 2:
        raise ValueError(
            f"Outcome column '{outcome_col}' must contain exactly two distinct "
            f"values; found {len(unique_vals)}."
        )

    # Resolve which value is positive / negative
    if positive_group is None:
        positive_group = unique_vals[0]
    if negative_group is None:
        negative_group = unique_vals[1] if unique_vals[0] == positive_group else unique_vals[0]

    group_pos = df[df[outcome_col] == positive_group][feature_col].dropna()
    group_neg = df[df[outcome_col] == negative_group][feature_col].dropna()

    n1 = len(group_pos)
    n2 = len(group_neg)
    if n1 < 2 or n2 < 2:
        raise ValueError("Each group must contain at least two observations.")

    mean1 = group_pos.mean()
    mean2 = group_neg.mean()
    var1 = group_pos.var(ddof=1)
    var2 = group_neg.var(ddof=1)

    # Pooled standard deviation
    pooled_std = np.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))
    if pooled_std == 0:
        raise ValueError("Pooled standard deviation is zero; cannot compute Cohen's d.")

    d = (mean1 - mean2) / pooled_std
    return d
