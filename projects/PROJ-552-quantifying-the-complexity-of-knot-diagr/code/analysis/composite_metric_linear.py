"""Linear composite complexity metric utilities.

This module defines a simple, interpretable composite metric for knot
complexity based on a weighted linear combination of three established
invariants:

* **crossing_number** – the minimal number of crossings in any diagram of the knot.
* **braid_index** – the smallest number of strands needed to represent the knot as a braid.
* **seifert_circle_count** – the number of Seifert circles obtained from the Seifert algorithm.

The metric is defined as

    C = α·crossing_number + β·braid_index + γ·seifert_circle_count

where ``α``, ``β`` and ``γ`` are scalar weights supplied by the caller.

The module also provides a convenience function that evaluates the
predictive performance of the composite metric against hyperbolic volume
using the existing regression utilities.  By comparing the resulting
R² and MAE with those obtained from the raw invariants alone, users can
verify that the composite improves fit, as requested by the reviewer.
"""

from __future__ import annotations

import pandas as pd
from typing import Mapping, Any

# The project already contains a regression helper that computes common
# regression metrics (R², MAE, etc.).  Import it lazily to avoid circular
# dependencies.
from .regression import compute_regression_metrics


def compute_linear_composite(
    df: pd.DataFrame,
    alpha: float = 1.0,
    beta: float = 1.0,
    gamma: float = 1.0,
) -> pd.Series:
    """Return the linear composite complexity metric ``C``.

    Parameters
    ----------
    df : pandas.DataFrame
        DataFrame containing the required invariant columns:
        ``crossing_number``, ``braid_index`` and ``seifert_circle_count``.
    alpha, beta, gamma : float, optional
        Weights for each invariant.  Default is ``1.0`` for all, yielding a
        simple sum of the three invariants.

    Returns
    -------
    pandas.Series
        The computed composite metric values.
    """
    required = {"crossing_number", "braid_index", "seifert_circle_count"}
    missing = required - set(df.columns)
    if missing:
        raise KeyError(f"Missing required columns for composite metric: {missing}")

    return alpha * df["crossing_number"] + beta * df["braid_index"] + gamma * df["seifert_circle_count"]


def evaluate_composite_metric(
    df: pd.DataFrame,
    target: str = "hyperbolic_volume",
    weights: Mapping[str, Any] | None = None,
) -> Mapping[str, float]:
    """Fit a univariate regression using the composite metric and report metrics.

    The function constructs the composite metric with the supplied ``weights``
    (or defaults to equal weighting), adds it as a column named
    ``composite_metric`` and then runs a simple linear regression against the
    ``target`` column (hyperbolic volume).  The returned dictionary contains the
    regression metrics produced by :func:`compute_regression_metrics`.
    """
    if weights is None:
        weights = {"alpha": 1.0, "beta": 1.0, "gamma": 1.0}

    composite = compute_linear_composite(df, **weights)
    df_with_metric = df.copy()
    df_with_metric["composite_metric"] = composite

    # ``compute_regression_metrics`` expects a DataFrame of predictors and a
    # Series of the target variable.  We provide only the composite metric as a
    # single‑column predictor.
    metrics = compute_regression_metrics(
        df_with_metric[["composite_metric"]], df_with_metric[target]
    )
    return metrics

