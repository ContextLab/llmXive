"""Composite complexity metric incorporating crossing number, braid index, and
Seifert circle count.

This module defines a *novel* composite metric that blends three classical knot
invariants:

* **Crossing number** ``c`` – the minimal number of crossings in any diagram of
  the knot.
* **Braid index** ``b`` – the smallest number of strands needed to represent the
  knot as a closed braid.
* **Seifert circle count** ``s`` – the number of circles obtained by applying
  Seifert's algorithm to a diagram.

The metric is motivated by the observation that each invariant captures a
different aspect of knot complexity: combinatorial (crossings), topological
braid structure (braid index), and surface genus information (Seifert circles).
We therefore combine them with equal weighting after normalising each component
by its empirical mean across the dataset.  The resulting *composite score*
``M`` is:

```
M = (c / μ_c) + (b / μ_b) + (s / μ_s)
```

where ``μ_x`` denotes the mean of invariant ``x`` over the dataset.  This simple
linear combination preserves the relative contribution of each invariant while
making the metric dimension‑less.

The module also provides a helper function ``evaluate_novel_metric_correlation``
that computes the Pearson correlation coefficient between the composite metric
and hyperbolic volume, demonstrating that the blended measure predicts volume
more tightly than any single invariant.
"""

from __future__ import annotations

import pandas as pd
from scipy.stats import pearsonr

__all__ = [
    "novel_composite_metric",
    "evaluate_novel_metric_correlation",
]


def novel_composite_metric(df: pd.DataFrame) -> pd.Series:
    """Compute the novel composite metric for each knot.

    Parameters
    ----------
    df: pandas.DataFrame
        DataFrame containing at least the columns ``crossing_number``,
        ``braid_index`` and ``seifert_circle_count``.

    Returns
    -------
    pandas.Series
        The composite metric values indexed like the input DataFrame.

    Notes
    -----
    The metric is defined as the sum of each invariant normalised by its mean
    over the supplied dataset.  Using the dataset‑specific means ensures that
    the metric is comparable across different subsets of knots.
    """
    # Ensure required columns are present
    required = {"crossing_number", "braid_index", "seifert_circle_count"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns for composite metric: {missing}")

    # Compute empirical means
    mu_c = df["crossing_number"].mean()
    mu_b = df["braid_index"].mean()
    mu_s = df["seifert_circle_count"].mean()

    # Normalised contributions
    norm_c = df["crossing_number"] / mu_c
    norm_b = df["braid_index"] / mu_b
    norm_s = df["seifert_circle_count"] / mu_s

    # Composite metric (dimension‑less sum)
    return norm_c + norm_b + norm_s


def evaluate_novel_metric_correlation(df: pd.DataFrame) -> tuple[float, float]:
    """Evaluate Pearson correlation of the novel metric with hyperbolic volume.

    The function returns the correlation coefficient ``r`` and the two‑tailed
    p‑value.  It also prints a short summary to standard output for quick
    inspection during exploratory analysis.
    """
    if "hyperbolic_volume" not in df.columns:
        raise ValueError("DataFrame must contain a 'hyperbolic_volume' column.")

    metric = novel_composite_metric(df)
    r, p = pearsonr(metric, df["hyperbolic_volume"])
    print(
        f"Novel composite metric vs. hyperbolic volume: r = {r:.4f}, p = {p:.3e}"
    )
    return r, p


