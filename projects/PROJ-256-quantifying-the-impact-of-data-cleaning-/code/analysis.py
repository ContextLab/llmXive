"""
Analysis utilities for the Quantifying Data Cleaning Impact project.

This module provides three public functions:

* ``run_baseline_analysis`` – orchestrates the baseline statistical analysis
  (t‑test, linear regression, Cohen's d) on a raw or pre‑loaded DataFrame.
* ``run_t_test`` – performs independent two‑sample t‑tests between the two
  outcome groups for each predictor.
* ``run_linear_regression`` – fits an OLS regression model predicting the
  outcome from the supplied predictors.

The implementation has been updated to correctly compute Cohen's d using
the pooled standard deviation of the two outcome groups (instead of the
global dataset standard deviation) as required by task **T1217**.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.api as sm

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Helper: Cohen's d with pooled standard deviation
# ----------------------------------------------------------------------
def _cohens_d_pooled(
    group0: pd.Series, group1: pd.Series
) -> float:
    """
    Compute Cohen's d using the pooled standard deviation of two groups.

    Parameters
    ----------
    group0, group1 : pd.Series
        Numeric series representing the two groups to compare.

    Returns
    -------
    float
        Cohen's d effect size. Returns ``np.nan`` if the pooled standard
        deviation is zero (to avoid division‑by‑zero).
    """
    n0, n1 = len(group0), len(group1)
    if n0 < 2 or n1 < 2:
        logger.debug(
            "Insufficient data for Cohen's d (n0=%s, n1=%s). Returning NaN.", n0, n1
        )
        return float("nan")

    var0 = group0.var(ddof=1)
    var1 = group1.var(ddof=1)

    # Pooled variance
    pooled_var = ((n0 - 1) * var0 + (n1 - 1) * var1) / (n0 + n1 - 2)
    if pooled_var <= 0:
        logger.debug(
            "Non‑positive pooled variance (%s). Returning NaN for Cohen's d.", pooled_var
        )
        return float("nan")

    pooled_std = np.sqrt(pooled_var)
    mean_diff = group1.mean() - group0.mean()
    d = mean_diff / pooled_std
    logger.debug(
        "Cohen's d computed: mean_diff=%.5f, pooled_std=%.5f, d=%.5f",
        mean_diff,
        pooled_std,
        d,
    )
    return d

# ----------------------------------------------------------------------
# Core analysis functions
# ----------------------------------------------------------------------
def run_t_test(
    df: pd.DataFrame,
    outcome: str,
    predictors: List[str],
) -> Dict[str, Any]:
    """
    Perform independent two‑sample t‑tests for each predictor.

    The outcome column is assumed binary (e.g., 0 vs 1). For each predictor,
    the function splits the rows into the two outcome groups and runs a
    ``scipy.stats.ttest_ind`` test.

    Returns a dictionary mapping predictor names to a sub‑dictionary with
    ``p_value`` and a 95 % confidence interval for the mean difference.
    """
    results: Dict[str, Any] = {}
    # Ensure the outcome column is binary
    if df[outcome].nunique() != 2:
        raise ValueError(
            f"Outcome column '{outcome}' must have exactly two distinct values."
        )
    group_vals = sorted(df[outcome].unique())
    grp0_val, grp1_val = group_vals[0], group_vals[1]

    for predictor in predictors:
        grp0 = df.loc[df[outcome] == grp0_val, predictor].dropna()
        grp1 = df.loc[df[outcome] == grp1_val, predictor].dropna()

        # Perform Welch's t‑test (unequal variances) – more robust.
        t_stat, p_val = stats.ttest_ind(grp0, grp1, equal_var=False)

        # Confidence interval for the difference of means
        diff = grp1.mean() - grp0.mean()
        se = np.sqrt(grp0.var(ddof=1) / len(grp0) + grp1.var(ddof=1) / len(grp1))
        ci_low = diff - 1.96 * se
        ci_high = diff + 1.96 * se

        results[predictor] = {
            "t_stat": float(t_stat),
            "p_value": float(p_val),
            "ci": [float(ci_low), float(ci_high)],
            "mean_diff": float(diff),
        }
        logger.debug(
            "T‑test for %s: t=%.4f, p=%.4f, CI=[%.4f, %.4f]",
            predictor,
            t_stat,
            p_val,
            ci_low,
            ci_high,
        )
    return results

def run_linear_regression(
    df: pd.DataFrame,
    outcome: str,
    predictors: List[str],
) -> Dict[str, Any]:
    """
    Fit an OLS linear regression model predicting ``outcome`` from ``predictors``.

    Returns a dictionary with coefficient estimates, their p‑values, the model
    R‑squared, and the overall F‑test p‑value.
    """
    X = df[predictors].copy()
    X = sm.add_constant(X)  # adds intercept term
    y = df[outcome]

    model = sm.OLS(y, X, missing="drop")
    results = model.fit()

    coeffs = results.params.to_dict()
    pvalues = results.pvalues.to_dict()
    summary = {
        "coefficients": {k: float(v) for k, v in coeffs.items()},
        "p_values": {k: float(v) for k, v in pvalues.items()},
        "r_squared": float(results.rsquared),
        "f_p_value": float(results.f_pvalue),
    }
    logger.debug(
        "Linear regression results: R²=%.4f, F‑test p=%.4f", results.rsquared, results.f_pvalue
    )
    return summary

# ----------------------------------------------------------------------
# Public entry point: run_baseline_analysis
# ----------------------------------------------------------------------
def run_baseline_analysis(
    *args,
    raw_dir: Optional[Union[str, Path]] = None,
    output_file: Optional[Union[str, Path]] = None,
    dataframe: Optional[pd.DataFrame] = None,
    outcome: Optional[str] = None,
    predictors: Optional[List[str]] = None,
    extra_kwargs_dict: Optional[Dict[str, Any]] = None,
    **kwargs,
) -> Dict[str, Any]:
    """
    Flexible baseline analysis driver.

    The function accepts a wide variety of call signatures to remain
    compatible with legacy scripts (see task **T1217** verification notes).

    Supported usage patterns include:

    * ``run_baseline_analysis()`` – discovers the default raw directory
      (``data/raw``) and writes results to ``data/processed/baseline_metrics.json``.
    * ``run_baseline_analysis(raw_dir, output_file)`` – positional raw and
      output paths.
    * ``run_baseline_analysis(dataframe=df, outcome='y', predictors=['x1','x2'])``
      – direct DataFrame input.
    * ``run_baseline_analysis(raw_dir='data/raw', output_file='data/processed/baseline.json',
      extra_kwargs_dict={...})`` – explicit keyword style.
    * ``run_baseline_analysis(dataframe=df, **extra_kwargs_dict)`` – any additional
      keyword arguments are ignored but accepted for backward compatibility.

    Returns
    -------
    dict
        Dictionary containing ``t_test``, ``linear_regression`` and
        ``cohens_d`` results.
    """
    # ------------------------------------------------------------------
    # Resolve arguments – give precedence to explicit keyword arguments.
    # ------------------------------------------------------------------
    if extra_kwargs_dict is None:
        extra_kwargs_dict = {}

    # Positional arguments handling (legacy)
    if args:
        # If the first positional arg looks like a path, treat it as raw_dir.
        if isinstance(args[0], (str, Path)):
            raw_dir = args[0]
        # If a second positional arg exists, treat it as output_file.
        if len(args) > 1 and isinstance(args[1], (str, Path)):
            output_file = args[1]

    # Merge any kwargs that were passed directly.
    raw_dir = raw_dir or kwargs.get("raw_dir")
    output_file = output_file or kwargs.get("output_file")
    dataframe = dataframe or kwargs.get("dataframe")
    outcome = outcome or kwargs.get("outcome")
    predictors = predictors or kwargs.get("predictors")

    # ------------------------------------------------------------------
    # Load data if a DataFrame wasn't supplied.
    # ------------------------------------------------------------------
    if dataframe is None:
        if not raw_dir:
            raise ValueError(
                "Either a DataFrame or a raw_dir must be provided to run_baseline_analysis."
            )
        raw_path = Path(raw_dir)
        # Find the first CSV file in the directory (convention used throughout the project).
        csv_files = list(raw_path.glob("*.csv"))
        if not csv_files:
            raise FileNotFoundError(f"No CSV files found in {raw_path}")
        dataframe = pd.read_csv(csv_files[0])
        logger.info("Loaded raw dataset from %s", csv_files[0])

    df = dataframe.copy()

    # ------------------------------------------------------------------
    # Infer outcome and predictor columns if not supplied.
    # ------------------------------------------------------------------
    if outcome is None:
        # Heuristic: first column named 'outcome' or the last column if binary.
        if "outcome" in df.columns:
            outcome = "outcome"
        else:
            # Pick the first binary column (0/1) as outcome.
            binary_cols = [
                col
                for col in df.columns
                if df[col].dropna().isin([0, 1]).all()
            ]
            if not binary_cols:
                raise ValueError("Unable to infer outcome column.")
            outcome = binary_cols[0]

    if predictors is None:
        predictors = [col for col in df.columns if col != outcome]

    # ------------------------------------------------------------------
    # Core statistical calculations.
    # ------------------------------------------------------------------
    t_test_results = run_t_test(df, outcome, predictors)
    regression_results = run_linear_regression(df, outcome, predictors)

    # Cohen's d – using the two outcome groups.
    group_vals = sorted(df[outcome].unique())
    if len(group_vals) != 2:
        raise ValueError(
            f"Outcome column '{outcome}' must have exactly two distinct values for Cohen's d."
        )
    grp0 = df.loc[df[outcome] == group_vals[0], outcome]
    grp1 = df.loc[df[outcome] == group_vals[1], outcome]
    cohens_d = _cohens_d_pooled(grp0, grp1)

    metrics: Dict[str, Any] = {
        "outcome_column": outcome,
        "predictors": predictors,
        "t_test": t_test_results,
        "linear_regression": regression_results,
        "cohens_d": float(cohens_d),
    }

    # ------------------------------------------------------------------
    # Write results if an output path was supplied.
    # ------------------------------------------------------------------
    if output_file:
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(metrics, f, indent=2)
        logger.info("Baseline metrics written to %s", output_path)

    return metrics

# The module's public interface
__all__ = [
    "run_baseline_analysis",
    "run_t_test",
    "run_linear_regression",
]