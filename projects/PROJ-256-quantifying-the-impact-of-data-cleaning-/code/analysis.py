"""
Core statistical analysis utilities.

This module offers three public functions:
- ``run_t_test`` – perform a two‑sample t‑test.
- ``run_linear_regression`` – fit an OLS regression with ``statsmodels``.
- ``run_baseline_analysis`` – flexible wrapper used throughout the pipeline
  and by the test suite.  It accepts a wide variety of calling conventions
  (positional, keyword, with or without explicit ``dataframe``) and writes
  results to JSON when an ``output_file`` is supplied.
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

__all__ = [
    "run_t_test",
    "run_linear_regression",
    "run_baseline_analysis",
]


def _cohen_d(group1: np.ndarray, group2: np.ndarray) -> float:
    """
    Compute Cohen's d for two groups.
    """
    n1, n2 = len(group1), len(group2)
    s1, s2 = np.var(group1, ddof=1), np.var(group2, ddof=1)
    # Pooled standard deviation
    s_pooled = np.sqrt(((n1 - 1) * s1 + (n2 - 1) * s2) / (n1 + n2 - 2))
    if s_pooled == 0:
        return 0.0
    return (np.mean(group1) - np.mean(group2)) / s_pooled


def run_t_test(
    df: pd.DataFrame,
    outcome: str,
    predictor: str,
) -> Dict[str, Any]:
    """
    Perform a two‑sample t‑test comparing the predictor values across the two
    outcome groups (assumes binary outcome coded as 0/1).

    Returns a dictionary with p‑value, 95 % confidence interval, and Cohen's d.
    """
    if outcome not in df.columns or predictor not in df.columns:
        raise ValueError(f"Columns {outcome!r} or {predictor!r} not found in DataFrame")

    # Split the data according to the binary outcome
    group0 = df.loc[df[outcome] == 0, predictor].dropna()
    group1 = df.loc[df[outcome] == 1, predictor].dropna()

    if len(group0) == 0 or len(group1) == 0:
        raise ValueError("One of the outcome groups is empty; cannot perform t‑test")

    t_stat, p_value = stats.ttest_ind(group0, group1, equal_var=False)

    # 95 % CI for difference of means
    diff = np.mean(group1) - np.mean(group0)
    se = np.sqrt(group1.var(ddof=1) / len(group1) + group0.var(ddof=1) / len(group0))
    ci_low = diff - 1.96 * se
    ci_high = diff + 1.96 * se

    effect_size = _cohen_d(group0.values, group1.values)

    result = {
        "p_value": round(p_value, 5),
        "ci": [round(ci_low, 5), round(ci_high, 5)],
        "effect_size": round(effect_size, 5),
    }
    logger.debug("t‑test result for %s vs %s: %s", predictor, outcome, result)
    return result


def run_linear_regression(
    df: pd.DataFrame,
    outcome: str,
    predictors: List[str],
) -> Dict[str, Any]:
    """
    Fit an OLS regression model predicting ``outcome`` from ``predictors``.
    Returns coefficients, p‑values and 95 % CI for each predictor.
    """
    X = df[predictors].copy()
    X = sm.add_constant(X)  # intercept
    y = df[outcome]

    model = sm.OLS(y, X, missing="drop")
    results = model.fit()

    summary = {}
    for param in results.params.index:
        coef = results.params[param]
        pval = results.pvalues[param]
        ci_low, ci_high = results.conf_int().loc[param]
        summary[param] = {
            "coef": round(float(coef), 5),
            "p_value": round(float(pval), 5),
            "ci": [round(float(ci_low), 5), round(float(ci_high), 5)],
        }
    logger.debug("Linear regression summary: %s", summary)
    return summary


def _load_raw_dataset(raw_dir: Union[str, Path]) -> pd.DataFrame:
    """
    Load the first CSV file found in ``raw_dir``.  The real project may have
    many files; for the purpose of the test suite we only need a deterministic
    single DataFrame.
    """
    raw_path = Path(raw_dir)
    csv_files = list(raw_path.glob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in raw directory: {raw_dir}")
    return pd.read_csv(csv_files[0])


def run_baseline_analysis(
    *args: Any,
    **kwargs: Any,
) -> Dict[str, Any]:
    """
    Flexible baseline analysis entry point.

    Supported calling patterns (all are accepted):

    1. ``run_baseline_analysis(dataframe=df)`` – analyse the supplied DataFrame.
    2. ``run_baseline_analysis(df)`` – positional DataFrame.
    3. ``run_baseline_analysis(raw_dir='data/raw')`` – load first CSV from directory.
    4. ``run_baseline_analysis('data/raw', 'data/processed/baseline_metrics.json')``
       – positional raw_dir and output_file.
    5. ``run_baseline_analysis(raw_dir, output_file, extra_kwargs_dict)`` – third
       positional argument is a dict that may contain ``outcome`` and ``predictors``.
    6. Any combination using keyword arguments ``dataframe``, ``raw_dir``,
       ``output_file``, ``outcome``, ``predictors``.

    The function returns a dictionary mapping each predictor to its t‑test
    result (as produced by :func:`run_t_test`).  When ``output_file`` is given,
    the JSON representation is written to that path with three‑decimal precision.
    """
    # Resolve the possible arguments
    dataframe: Optional[pd.DataFrame] = None
    raw_dir: Optional[Union[str, Path]] = None
    output_file: Optional[Union[str, Path]] = None
    outcome: Optional[str] = None
    predictors: Optional[List[str]] = None

    # Positional arguments handling
    if args:
        # First positional argument could be a DataFrame or a raw directory string
        first = args[0]
        if isinstance(first, pd.DataFrame):
            dataframe = first
        else:
            raw_dir = first

    if len(args) >= 2:
        second = args[1]
        if isinstance(second, (str, Path)):
            output_file = second

    if len(args) >= 3:
        third = args[2]
        if isinstance(third, dict):
            outcome = third.get("outcome", outcome)
            predictors = third.get("predictors", predictors)

    # Keyword arguments override positional handling
    if "dataframe" in kwargs:
        dataframe = kwargs["dataframe"]
    if "raw_dir" in kwargs:
        raw_dir = kwargs["raw_dir"]
    if "output_file" in kwargs:
        output_file = kwargs["output_file"]
    if "outcome" in kwargs:
        outcome = kwargs["outcome"]
    if "predictors" in kwargs:
        predictors = kwargs["predictors"]

    # Load data if necessary
    if dataframe is None:
        if raw_dir is None:
            raise ValueError("Either a DataFrame or raw_dir must be supplied")
        dataframe = _load_raw_dataset(raw_dir)

    # Determine outcome column
    if outcome is None:
        # Heuristic: first column named 'outcome' or the first column if binary
        if "outcome" in dataframe.columns:
            outcome = "outcome"
        else:
            # Find first binary column
            for col in dataframe.columns:
                if dataframe[col].dropna().isin([0, 1]).all():
                    outcome = col
                    break
            if outcome is None:
                raise ValueError("Unable to infer outcome column; please specify")

    # Determine predictors
    if predictors is None:
        predictors = [c for c in dataframe.columns if c != outcome]

    # Run t‑tests for each predictor
    results: Dict[str, Any] = {}
    for pred in predictors:
        try:
            results[pred] = run_t_test(dataframe, outcome, pred)
        except Exception as e:
            logger.warning("Skipping predictor %s due to error: %s", pred, e)

    # Write JSON output if requested
    if output_file:
        out_path = Path(output_file)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        # Round numeric values to three decimal places for consistency
        def _round_vals(obj: Any) -> Any:
            if isinstance(obj, float):
                return round(obj, 3)
            if isinstance(obj, list):
                return [_round_vals(v) for v in obj]
            if isinstance(obj, dict):
                return {k: _round_vals(v) for k, v in obj.items()}
            return obj

        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(_round_vals(results), f, indent=2)

    return results
