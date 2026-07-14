"""
analysis.py
-------------
Core analysis utilities for the project.

Provides a flexible `run_baseline_analysis` function that can be invoked
with a variety of signatures as required by the many task scripts in the
code base. The function performs:
  * A two‑sample t‑test on an outcome variable split by the median of a
    predictor.
  * A simple linear regression (OLS) of the outcome on the predictor.
  * Effect‑size calculations (Cohen's d for the t‑test and R² for the regression).
  * 95 % confidence intervals for the mean difference (t‑test) and the
    regression coefficient.

The results are written to a JSON file when an ``output_file`` argument is
supplied, otherwise the metric dictionary is returned.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional, Union

import numpy as np
import pandas as pd
import scipy.stats as stats
import statsmodels.api as sm

logger = logging.getLogger(__name__)

def _select_numeric_columns(df: pd.DataFrame) -> list:
    """Return a list of column names that contain numeric data."""
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    return numeric_cols

def _determine_outcome_and_predictor(df: pd.DataFrame) -> tuple:
    """
    Heuristic to pick an outcome and a predictor column.

    - The *outcome* is the first numeric column.
    - The *predictor* is the second numeric column (if available).
    If only one numeric column exists, the predictor is the same column
    (the regression will be degenerate but still yields a coefficient of 1).
    """
    numeric_cols = _select_numeric_columns(df)
    if not numeric_cols:
        raise ValueError("Dataframe contains no numeric columns for analysis.")
    outcome = numeric_cols[0]
    predictor = numeric_cols[1] if len(numeric_cols) > 1 else numeric_cols[0]
    return outcome, predictor

def _cohen_d(group1: np.ndarray, group2: np.ndarray) -> float:
    """Compute Cohen's d using the pooled standard deviation."""
    n1, n2 = len(group1), len(group2)
    s1, s2 = np.var(group1, ddof=1), np.var(group2, ddof=1)
    pooled_sd = np.sqrt(((n1 - 1) * s1 + (n2 - 1) * s2) / (n1 + n2 - 2))
    if pooled_sd == 0:
        return 0.0
    return (np.mean(group1) - np.mean(group2)) / pooled_sd

def _confidence_interval_mean_diff(data1: np.ndarray, data2: np.ndarray, confidence: float = 0.95) -> tuple:
    """Return the two‑sided confidence interval for the difference of means."""
    diff = np.mean(data1) - np.mean(data2)
    se = np.sqrt(np.var(data1, ddof=1) / len(data1) + np.var(data2, ddof=1) / len(data2))
    df = len(data1) + len(data2) - 2
    t_crit = stats.t.ppf((1 + confidence) / 2.0, df)
    margin = t_crit * se
    return diff - margin, diff + margin

def _confidence_interval_coef(model: sm.regression.linear_model.RegressionResultsWrapper,
                             confidence: float = 0.95) -> tuple:
    """Confidence interval for the slope coefficient of an OLS model."""
    params = model.params
    conf_int = model.conf_int(alpha=1 - confidence)
    # conf_int returns a DataFrame with rows for each parameter; slope is the second row (index 1)
    lower, upper = conf_int.iloc[1].tolist()
    return lower, upper

def _run_analysis_on_dataframe(df: pd.DataFrame,
                               outcome: Optional[str] = None,
                               predictor: Optional[str] = None) -> Dict[str, Any]:
    """
    Perform the statistical analysis on a single dataframe.

    Returns a dict with the structure:
    {
        "t_test": {"p_value": ..., "ci": [low, high], "cohen_d": ...},
        "linear_regression": {"p_value": ..., "ci": [low, high], "r_squared": ...}
    }
    """
    if outcome is None or predictor is None:
        outcome, predictor = _determine_outcome_and_predictor(df)

    logger.debug(f"Selected outcome column '{outcome}' and predictor column '{predictor}'")

    # --- t‑test ---------------------------------------------------------
    median_pred = df[predictor].median()
    group_low = df[df[predictor] <= median_pred][outcome].dropna().values
    group_high = df[df[predictor] > median_pred][outcome].dropna().values

    if len(group_low) == 0 or len(group_high) == 0:
        raise ValueError("Insufficient data after splitting for t‑test.")

    t_stat, p_value = stats.ttest_ind(group_low, group_high, equal_var=False)
    ci_low, ci_high = _confidence_interval_mean_diff(group_low, group_high)

    d = _cohen_d(group_low, group_high)

    # --- linear regression -----------------------------------------------
    X = sm.add_constant(df[predictor].astype(float))
    y = df[outcome].astype(float)
    model = sm.OLS(y, X).fit()

    slope_p = model.pvalues[1]  # index 1 corresponds to the predictor coefficient
    r_squared = model.rsquared
    ci_reg_low, ci_reg_high = _confidence_interval_coef(model)

    result = {
        "t_test": {
            "p_value": round(float(p_value), 6),
            "ci": [round(float(ci_low), 6), round(float(ci_high), 6)],
            "cohen_d": round(float(d), 6)
        },
        "linear_regression": {
            "p_value": round(float(slope_p), 6),
            "ci": [round(float(ci_reg_low), 6), round(float(ci_reg_high), 6)],
            "r_squared": round(float(r_squared), 6)
        }
    }
    return result

def run_baseline_analysis(*args,
                          dataframe: Optional[pd.DataFrame] = None,
                          raw_dir: Optional[Union[str, Path]] = None,
                          outcome: Optional[str] = None,
                          predictors: Optional[list] = None,
                          output_file: Optional[Union[str, Path]] = None,
                          **kwargs) -> Union[Dict[str, Any], int]:
    """
    Flexible entry point used throughout the project.

    Supported calling patterns (all are accepted):
    1. ``run_baseline_analysis(dataframe=df)`` – analyse an in‑memory DataFrame.
    2. ``run_baseline_analysis(dataframe=df, outcome='y', predictors=['x1','x2'])``
    3. ``run_baseline_analysis(raw_dir='data/raw', output_file='data/processed/baseline_metrics.json')``
    4. ``run_baseline_analysis('data/raw', 'data/processed/baseline_metrics.json')``
    5. ``run_baseline_analysis(raw_dir, output_file, extra_kwargs_dict)`` – any extra
       keyword arguments are ignored for backward compatibility.

    The function returns the metrics dictionary when called programmatically.
    When ``output_file`` is supplied the metrics are written to that path and the
    function returns ``0`` (convention used by the original scripts).

    Parameters
    ----------
    dataframe: Optional[pd.DataFrame]
        Direct DataFrame to analyse.
    raw_dir: Optional[str|Path]
        Directory containing raw CSV files. All ``*.csv`` files are analysed
        and their individual results are aggregated.
    outcome: Optional[str]
        Name of the outcome column (only used when ``dataframe`` is supplied).
    predictors: Optional[list]
        List of predictor column names – the first element is used.
    output_file: Optional[str|Path]
        Destination JSON file for aggregated results.
    *args, **kwargs:
        Accepted for backward compatibility; they are interpreted as positional
        ``raw_dir`` and ``output_file`` when ``dataframe`` is not provided.
    """
    logger = logging.getLogger(__name__)

    # Resolve positional arguments when no explicit keywords are given
    if dataframe is None and not raw_dir:
        # Possible signatures:
        #   run_baseline_analysis('data/raw', 'data/processed/baseline_metrics.json')
        #   run_baseline_analysis('data/raw', 'data/processed/baseline_metrics.json', extra_dict)
        if len(args) >= 1:
            raw_dir = args[0]
        if len(args) >= 2:
            output_file = args[1]

    # ------------------------------------------------------------------
    # Case A: a DataFrame is directly supplied
    # ------------------------------------------------------------------
    if isinstance(dataframe, pd.DataFrame):
        logger.debug("Running baseline analysis on supplied DataFrame.")
        metrics = _run_analysis_on_dataframe(dataframe, outcome=outcome,
                                             predictor=(predictors[0] if predictors else None))
        if output_file:
            Path(output_file).parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, "w") as fp:
                json.dump(metrics, fp, indent=2)
            return 0
        return metrics

    # ------------------------------------------------------------------
    # Case B: analyse all CSV files in a directory
    # ------------------------------------------------------------------
    if raw_dir is None:
        raise ValueError("Either a DataFrame or a raw_dir must be supplied to run analysis.")

    raw_path = Path(raw_dir)
    if not raw_path.is_dir():
        raise FileNotFoundError(f"Raw directory '{raw_dir}' does not exist.")

    aggregated = {}
    csv_files = list(raw_path.glob("*.csv"))
    if not csv_files:
        logger.warning(f"No CSV files found in raw directory '{raw_dir}'.")
    for csv_file in csv_files:
        try:
            df = pd.read_csv(csv_file)
            logger.debug(f"Analyzing file {csv_file.name}")
            metrics = _run_analysis_on_dataframe(df)
            aggregated[csv_file.name] = metrics
        except Exception as exc:
            logger.error(f"Failed to analyse {csv_file.name}: {exc}")

    if output_file:
        out_path = Path(output_file)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with out_path.open("w") as fp:
            json.dump(aggregated, fp, indent=2)
        logger.info(f"Baseline analysis written to {out_path}")
        return 0
    return aggregated
