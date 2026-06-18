"""Regression analysis utilities.

This module provides functions to compute Pearson and Spearman correlation
coefficients between the primary combinatorial invariants (crossing number
and braid index) and to calculate simple effect‑size metrics (Cohen's d
and the correlation coefficient *r*).  All output is written to
``data/analysis/correlation_effects_report.json``.

The implementation deliberately omits *p‑values* because the dataset
comprises the entire census of prime knots (a census dataset).  Per
FR‑006 and Constitution Principle VII we mark p‑values as
“not applicable for census data”.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Tuple

import numpy as np
import pandas as pd
from scipy.stats import pearsonr, spearmanr

from analysis._utils import load_cleaned_knots
from reproducibility.logs import get_logger, log_operation


@dataclass
class CorrelationResult:
    """Pearson and Spearman correlation coefficients."""
    pearson_r: float
    spearman_rho: float


@dataclass
class EffectSizeResult:
    """Effect‑size metrics derived from the correlations."""
    cohen_d: float
    r: float  # same as Pearson r for convenience


@log_operation
def compute_correlations_and_effect_sizes(df: pd.DataFrame) -> Tuple[CorrelationResult, EffectSizeResult]:
    """
    Compute Pearson and Spearman correlations between ``crossing_number`` and
    ``braid_index``.  Also compute Cohen's d for the difference between
    *alternating* and *non‑alternating* knots (using ``crossing_number`` as the
    quantitative variable).  The Pearson correlation coefficient is returned
    as ``r`` in the :class:`EffectSizeResult` for downstream consistency.

    Parameters
    ----------
    df:
        DataFrame that must contain the columns
        ``crossing_number``, ``braid_index`` and ``alternating`` (boolean or
        ``'alternating'``/``'non-alternating'`` strings).

    Returns
    -------
    tuple[CorrelationResult, EffectSizeResult]
        The first element holds the two correlation coefficients, the second
        holds Cohen's d and the Pearson r (re‑exposed as ``r``).
    """
    logger = get_logger(__name__)
    logger.info("Starting correlation and effect‑size computation")

    # --------------------------------------------------------------
    # 1. Correlations
    # --------------------------------------------------------------
    # Defensive: drop rows with missing values in the two columns we need.
    corr_df = df.dropna(subset=["crossing_number", "braid_index"])
    x = corr_df["crossing_number"].astype(float)
    y = corr_df["braid_index"].astype(float)

    if len(x) == 0:
        raise ValueError("No data available for correlation computation.")

    pearson_r, _ = pearsonr(x, y)  # p‑value ignored deliberately
    spearman_rho, _ = spearmanr(x, y)  # p‑value ignored deliberately

    corr_res = CorrelationResult(pearson_r=pearson_r, spearman_rho=spearman_rho)
    logger.debug("Pearson r=%s, Spearman rho=%s", pearson_r, spearman_rho)

    # --------------------------------------------------------------
    # 2. Cohen's d between alternating / non‑alternating groups
    # --------------------------------------------------------------
    # Normalise the ``alternating`` column to a boolean.
    alt_series = df["alternating"].apply(
        lambda v: True if str(v).lower() in {"alternating", "true", "1"} else False
    )
    group_a = df.loc[alt_series, "crossing_number"].astype(float)
    group_b = df.loc[~alt_series, "crossing_number"].astype(float)

    if len(group_a) == 0 or len(group_b) == 0:
        raise ValueError("Both alternating and non‑alternating groups must be present.")

    mean_a, mean_b = group_a.mean(), group_b.mean()
    var_a, var_b = group_a.var(ddof=1), group_b.var(ddof=1)
    n_a, n_b = len(group_a), len(group_b)

    # Pooled standard deviation
    pooled_sd = np.sqrt(((n_a - 1) * var_a + (n_b - 1) * var_b) / (n_a + n_b - 2))
    cohen_d = (mean_a - mean_b) / pooled_sd if pooled_sd != 0 else 0.0

    effect_res = EffectSizeResult(cohen_d=cohen_d, r=pearson_r)
    logger.debug("Cohen's d=%s", cohen_d)

    return corr_res, effect_res


@log_operation
def write_correlation_effects_report(
    output_path: Path,
    corr: CorrelationResult,
    effect: EffectSizeResult,
) -> None:
    """
    Serialize the correlation and effect‑size results to JSON.

    The JSON contains an explicit note that p‑values are not applicable for
    census data.
    """
    report = {
        "pearson_r": corr.pearson_r,
        "spearman_rho": corr.spearman_rho,
        "cohen_d": effect.cohen_d,
        "r_effect_size": effect.r,
        "p_values": "not applicable for census data",
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    logger = get_logger(__name__)
    logger.info("Correlation‑effect report written to %s", output_path)


@log_operation
def main() -> None:
    """
    Entry‑point used by the quick‑start script.

    Loads the cleaned knot dataset, computes the metrics and writes the
    JSON report to ``data/analysis/correlation_effects_report.json``.
    """
    df = load_cleaned_knots()
    corr_res, effect_res = compute_correlations_and_effect_sizes(df)
    out_path = Path("data/analysis/correlation_effects_report.json")
    write_correlation_effects_report(out_path, corr_res, effect_res)
    print(f"Correlation and effect‑size report saved to {out_path}")