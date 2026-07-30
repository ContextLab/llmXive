"""
Baseline analysis utilities.

This module provides three public callables:

* ``run_t_test`` – perform an independent two‑sample t‑test and return
  p‑value, 95 % confidence interval and Cohen's d.
* ``run_linear_regression`` – fit an OLS regression with statsmodels and
  return the model p‑value (F‑test) and R².
* ``run_baseline_analysis`` – orchestrate the baseline analysis over one
  dataframe *or* over a directory of raw CSV files and write the results
  to ``data/processed/baseline_metrics.json``.

The implementation is deliberately tolerant of a wide range of calling
conventions because many legacy task scripts invoke the function with
different argument patterns.
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
import scipy.stats
import statsmodels.api as sm

from config import get_config

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Helper: identify outcome and predictor columns
# ----------------------------------------------------------------------
def _infer_columns(df: pd.DataFrame) -> Tuple[str, List[str]]:
    """
    Heuristically pick an outcome column and a list of predictor columns.

    Preference order for the outcome column:
    1. ``target``
    2. ``y``
    3. ``outcome``
    4. The last numeric column in the frame.

    All remaining numeric columns are treated as predictors.
    """
    outcome_candidates = ["target", "y", "outcome"]
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

    outcome = None
    for cand in outcome_candidates:
        if cand in df.columns and cand in numeric_cols:
            outcome = cand
            break

    if outcome is None and numeric_cols:
        outcome = numeric_cols[-1]  # fallback to last numeric column

    predictors = [c for c in numeric_cols if c != outcome]
    return outcome, predictors

# ----------------------------------------------------------------------
# Helper: find a binary grouping column for t‑test
# ----------------------------------------------------------------------
def _find_group_column(df: pd.DataFrame) -> Optional[str]:
    """
    Return the name of the first column that has exactly two unique values
    (ignoring NaNs).  Preference is given to non‑numeric columns, but numeric
    columns with two distinct values are also accepted.
    """
    for col in df.columns:
        unique_vals = df[col].dropna().unique()
        if len(unique_vals) == 2:
            return col
    return None

# ----------------------------------------------------------------------
# T‑test implementation
# ----------------------------------------------------------------------
def run_t_test(
    df: pd.DataFrame,
    outcome: str,
    group_col: str,
) -> Dict[str, Any]:
    """
    Perform a Welch's t‑test (unequal variances) between the two groups
    defined by ``group_col`` on the numeric ``outcome`` column.

    Returns a dictionary with keys ``p_value``, ``ci`` (list ``[low, high]``)
    and ``cohen_d``.  All numeric values are rounded to three decimal places.
    """
    groups = df[[outcome, group_col]].dropna()
    g1 = groups[groups[group_col] == groups[group_col].unique()[0]][outcome].values
    g2 = groups[groups[group_col] == groups[group_col].unique()[1]][outcome].values

    # Guard against empty groups
    if len(g1) == 0 or len(g2) == 0:
        raise ValueError("One of the groups is empty – cannot perform t‑test.")

    # Welch's t‑test
    t_res = scipy.stats.ttest_ind(g1, g2, equal_var=False)
    p_val = float(t_res.pvalue)

    # Mean difference and confidence interval for the difference of means
    diff = np.mean(g1) - np.mean(g2)
    se = np.sqrt(np.var(g1, ddof=1) / len(g1) + np.var(g2, ddof=1) / len(g2))
    ci_low = diff - 1.96 * se
    ci_high = diff + 1.96 * se

    # Cohen's d (pooled standard deviation)
    s1 = np.std(g1, ddof=1)
    s2 = np.std(g2, ddof=1)
    n1, n2 = len(g1), len(g2)
    pooled_sd = np.sqrt(((n1 - 1) * s1 ** 2 + (n2 - 1) * s2 ** 2) / (n1 + n2 - 2))
    cohen_d = diff / pooled_sd if pooled_sd != 0 else float("nan")

    return {
        "p_value": round(p_val, 3),
        "ci": [round(ci_low, 3), round(ci_high, 3)],
        "cohen_d": round(cohen_d, 3) if not np.isnan(cohen_d) else None,
    }

# ----------------------------------------------------------------------
# Linear regression implementation
# ----------------------------------------------------------------------
def run_linear_regression(
    df: pd.DataFrame,
    outcome: str,
    predictors: List[str],
) -> Dict[str, Any]:
    """
    Fit an OLS regression ``outcome ~ predictors`` using statsmodels.

    Returns a dictionary with keys ``p_value`` (model F‑test) and ``r_squared``.
    Values are rounded to three decimal places.
    """
    if not predictors:
        raise ValueError("No predictor columns available for regression.")

    X = df[predictors].copy()
    X = sm.add_constant(X, has_constant="add")
    y = df[outcome]

    model = sm.OLS(y, X, missing="drop").fit()
    p_val = float(model.f_pvalue) if model.f_pvalue is not None else None
    r2 = float(model.rsquared) if model.rsquared is not None else None

    return {
        "p_value": round(p_val, 3) if p_val is not None else None,
        "r_squared": round(r2, 3) if r2 is not None else None,
    }

# ----------------------------------------------------------------------
# Core orchestrator – flexible signature
# ----------------------------------------------------------------------
def run_baseline_analysis(*args, **kwargs) -> Dict[str, Any]:
    """
    Compute baseline metrics.

    Supported calling conventions (all are accepted):

    * ``run_baseline_analysis()`` – uses defaults from ``code.config``.
    * ``run_baseline_analysis(raw_dir, output_file)`` – positional raw and output.
    * ``run_baseline_analysis(raw_dir=..., output_file=...)`` – keyword form.
    * ``run_baseline_analysis(raw_dir, output_file, extra_kwargs_dict)`` – third
      positional argument is ignored (kept for legacy compatibility).
    * ``run_baseline_analysis(dataframe=df)`` – analyse a single dataframe.
    * ``run_baseline_analysis(dataframe=df, outcome='y', predictors=['x1','x2'])``
      – explicit column specification.

    The function returns a dictionary mapping dataset identifiers to their
    metric dictionaries.  When a directory is processed the result is also
    written to the ``output_file`` path (creating parent directories as needed).
    """
    # ------------------------------------------------------------------
    # Resolve arguments
    # ------------------------------------------------------------------
    raw_dir: Optional[str] = None
    output_file: Optional[str] = None
    dataframe: Optional[pd.DataFrame] = None
    outcome: Optional[str] = None
    predictors: Optional[List[str]] = None

    # Positional arguments handling
    if args:
        # ``raw_dir`` may be first positional argument
        if len(args) >= 1:
            raw_dir = args[0]
        if len(args) >= 2:
            output_file = args[1]
        # third positional argument is historic ``extra_kwargs_dict`` – ignore
    
    # Keyword arguments handling
    raw_dir = kwargs.get("raw_dir", raw_dir)
    output_file = kwargs.get("output_file", output_file)
    dataframe = kwargs.get("dataframe", dataframe)
    outcome = kwargs.get("outcome", outcome)
    predictors = kwargs.get("predictors", predictors)

    # Default locations from the global config if not explicitly supplied
    cfg = get_config()
    if raw_dir is None:
        raw_dir = cfg.get("RAW_DATA_PATH", "data/raw")
    if output_file is None:
        processed_dir = cfg.get("PROCESSED_DATA_PATH", "data/processed")
        output_file = os.path.join(processed_dir, "baseline_metrics.json")

    results: Dict[str, Any] = {}

    # ------------------------------------------------------------------
    # Single‑dataframe mode
    # ------------------------------------------------------------------
    if isinstance(dataframe, pd.DataFrame):
        df = dataframe.copy()
        if outcome is None:
            outcome, _ = _infer_columns(df)
        if outcome is None:
            raise ValueError("Unable to infer outcome column.")
        group_col = _find_group_column(df)
        if group_col is None:
            raise ValueError("No suitable binary group column found for t‑test.")

        # Compute metrics
        t_res = run_t_test(df, outcome, group_col)
        _, pred_cols = _infer_columns(df)
        lin_res = {}
        if pred_cols:
            lin_res = run_linear_regression(df, outcome, pred_cols)

        results["single_dataframe"] = {
            "t_test": t_res,
            "linear_regression": lin_res,
        }
        return results

    # ------------------------------------------------------------------
    # Directory mode – iterate over CSV/TSV files
    # ------------------------------------------------------------------
    raw_path = Path(raw_dir)
    if not raw_path.is_dir():
        raise FileNotFoundError(f"Raw data directory not found: {raw_dir}")

    for file_path in raw_path.iterdir():
        if file_path.suffix.lower() not in {".csv", ".tsv", ".txt"}:
            continue  # skip non‑tabular files

        try:
            df = pd.read_csv(file_path)
        except Exception as exc:
            logger.warning("Failed to read %s: %s", file_path.name, exc)
            continue

        # Infer columns
        outcome_col, predictor_cols = _infer_columns(df)
        if outcome_col is None:
            logger.warning("Could not infer outcome column in %s – skipping.", file_path.name)
            continue

        group_col = _find_group_column(df)
        if group_col is None:
            logger.warning("No binary grouping column in %s – skipping t‑test.", file_path.name)
            continue

        # Run analyses
        try:
            t_metrics = run_t_test(df, outcome_col, group_col)
        except Exception as exc:
            logger.warning("t‑test failed for %s: %s", file_path.name, exc)
            t_metrics = {}

        lin_metrics: Dict[str, Any] = {}
        if predictor_cols:
            try:
                lin_metrics = run_linear_regression(df, outcome_col, predictor_cols)
            except Exception as exc:
                logger.warning("Regression failed for %s: %s", file_path.name, exc)

        dataset_key = file_path.stem
        results[dataset_key] = {
            "t_test": t_metrics,
            "linear_regression": lin_metrics,
        }

    # ------------------------------------------------------------------
    # Write results to JSON (ensuring the directory exists)
    # ------------------------------------------------------------------
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, sort_keys=True)

    logger.info("Baseline metrics written to %s (%d datasets)", output_path, len(results))
    return results

# ----------------------------------------------------------------------
# Simple CLI entry point
# ----------------------------------------------------------------------
def main() -> None:
    """
    CLI entry point used by ``python -m code.analysis`` or the legacy
    ``t012_run_baseline_analysis.py`` script.
    """
    setup_logging = None
    try:
        from utils import setup_logging  # type: ignore
    except Exception:
        pass

    if setup_logging:
        setup_logging(log_level="INFO")

    run_baseline_analysis()

if __name__ == "__main__":
    main()