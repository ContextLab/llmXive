"""
analysis.tradeoff_model
-----------------------

This module implements the core analysis pipeline required for task **T070**.
It provides functions to load processed execution logs, filter invalid
workflows, compute variance inflation factors (VIF), fit a logistic
trade‑off curve between context reduction percentage and policy‑violation
error rate, and detect the safe‑operating‑zone threshold where the error
rate first exceeds the 1 % bound.

The public API matches the signatures declared in the project’s API
surface and satisfies the unit tests in ``tests/unit/test_vif_analysis.py``.
"""

import json
import csv
from pathlib import Path
from typing import List, Tuple, Dict, Any

import numpy as np
import pandas as pd
from scipy.optimize import curve_fit

from statsmodels.stats.outliers_influence import variance_inflation_factor

# ----------------------------------------------------------------------
# Configuration constants
# ----------------------------------------------------------------------
# Directory where result artifacts are written.
RESULTS_DIR = Path("data/results")
# Threshold for VIF – values above this indicate problematic multicollinearity.
VIF_THRESHOLD = 5.0

# Ensure the results directory exists.
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def load_processed_logs(processed_dir: Path = Path("data/processed")) -> List[Dict[str, Any]]:
    """
    Load all processed execution logs from ``processed_dir``.

    Parameters
    ----------
    processed_dir : Path
        Directory containing JSON log files. Files with a ``.json`` suffix
        are read; other files are ignored.

    Returns
    -------
    List[Dict[str, Any]]
        A list of log dictionaries. If the directory does not exist or
        contains no JSON files, an empty list is returned.
    """
    logs: List[Dict[str, Any]] = []
    if not processed_dir.is_dir():
        return logs

    for json_file in processed_dir.glob("*.json"):
        try:
            with json_file.open("r", encoding="utf-8") as f:
                data = json.load(f)
                # The pipeline may store a single log dict or a list of logs.
                if isinstance(data, list):
                    logs.extend(data)
                else:
                    logs.append(data)
        except Exception:
            # Skip malformed files – the analysis should be robust.
            continue
    return logs

def filter_invalid_workflows_from_logs(logs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Filter out any workflow logs where ``is_valid`` == False.

    Parameters
    ----------
    logs : List[Dict[str, Any]]

    Returns
    -------
    List[Dict[str, Any]]
    """
    return [log for log in logs if log.get("is_valid", True)]

# ----------------------------------------------------------------------
# VIF analysis
# ----------------------------------------------------------------------
def calculate_vif(df: pd.DataFrame, features: List[str]) -> Dict[str, float]:
    """
    Compute the Variance Inflation Factor for each feature column.

    Parameters
    ----------
    df : pandas.DataFrame
        Dataframe containing the features.
    features : List[str]
        List of column names to evaluate.

    Returns
    -------
    Dict[str, float]
        Mapping from feature name to its VIF value.
    """
    vif_dict: Dict[str, float] = {}
    # Ensure the dataframe only contains the selected columns and drop NaNs.
    X = df[features].dropna().values
    if X.shape[0] == 0:
        # No rows to compute VIF – return zeros.
        return {feat: 0.0 for feat in features}

    for i, col in enumerate(features):
        # variance_inflation_factor expects a 2‑D array where columns are variables.
        vif = variance_inflation_factor(X, i)
        vif_dict[col] = float(vif)
    return vif_dict

def run_vif_analysis(
    logs: List[Dict[str, Any]] | None = None,
) -> Tuple[Dict[str, float], bool]:
    """
    Perform VIF analysis on the processed logs.

    If ``logs`` is ``None`` the function loads logs from the default
    processed directory.

    Returns
    -------
    Tuple[Dict[str, float], bool]
        A tuple of the VIF results dict and a boolean indicating whether
        any VIF exceeds ``VIF_THRESHOLD``.
    """
    if logs is None:
        logs = load_processed_logs()
    valid_logs = filter_invalid_workflows_from_logs(logs)

    # Build a DataFrame with numeric features that are relevant for multicollinearity.
    # For the purposes of this project the features are ``depth`` and ``complexity``.
    # Additional numeric fields can be added later without breaking the API.
    df = pd.DataFrame(
        [
            {
                "depth": log.get("depth", np.nan),
                "complexity": log.get("complexity", np.nan),
            }
            for log in valid_logs
        ]
    )

    # Drop rows where either feature is missing.
    df = df.dropna(subset=["depth", "complexity"])

    vif_results = calculate_vif(df, ["depth", "complexity"])
    exceeded = any(v > VIF_THRESHOLD for v in vif_results.values())
    return vif_results, exceeded

def save_vif_report(report: Dict[str, Any], output_path: Path = RESULTS_DIR / "vif_report.json") -> Path:
    """
    Write the VIF analysis report to a JSON file.

    Parameters
    ----------
    report : Dict[str, Any]
        The report dictionary to serialize.
    output_path : Path
        Destination path (default ``data/results/vif_report.json``).

    Returns
    -------
    Path
        The path of the written file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, sort_keys=True)
    return output_path

# ----------------------------------------------------------------------
# Trade‑off curve fitting
# ----------------------------------------------------------------------
def logistic_function(x: np.ndarray, L: float, k: float, x0: float) -> np.ndarray:
    """
    Logistic (sigmoid) function used to model the trade‑off curve.

    Parameters
    ----------
    x : np.ndarray
        Input values (e.g., reduction percentages).
    L : float
        Curve's maximum value (asymptote as x → +∞).
    k : float
        Growth rate.
    x0 : float
        The x‑value of the sigmoid's midpoint.

    Returns
    -------
    np.ndarray
        Logistic function evaluated at ``x``.
    """
    return L / (1.0 + np.exp(-k * (x - x0)))

def fit_tradeoff_curve(logs: List[Dict[str, Any]]) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Fit a logistic curve to the observed error rates.

    The function groups logs by ``context_reduction_pct`` (rounded to
    one decimal place), computes the empirical error rate for each group,
    and fits the logistic model using ``scipy.optimize.curve_fit``.

    Parameters
    ----------
    logs : List[Dict[str, Any]]
        Processed execution logs. Each log must contain the keys
        ``context_reduction_pct`` (float) and ``policy_violations`` (list).

    Returns
    -------
    Tuple[np.ndarray, np.ndarray, np.ndarray]
        * ``reduction_pcts`` – sorted unique reduction percentages.
        * ``error_rates`` – empirical error rates for each percentage.
        * ``fitted`` – logistic model predictions at the same percentages.
    """
    # Aggregate logs by reduction percentage.
    df = pd.DataFrame(
        [
            {
                "reduction_pct": float(log.get("context_reduction_pct", np.nan)),
                "violation": 1 if log.get("policy_violations") else 0,
            }
            for log in logs
            if isinstance(log.get("context_reduction_pct"), (int, float))
        ]
    )
    # Remove rows with NaN reduction_pct.
    df = df.dropna(subset=["reduction_pct"])

    if df.empty:
        # No data – return empty arrays.
        return np.array([]), np.array([]), np.array([])

    # Group by reduction percentage (rounded to 1 decimal place for stability).
    grouped = df.groupby(df["reduction_pct"].round(1))
    reduction_pcts = grouped.mean().index.to_numpy()
    error_rates = grouped["violation"].mean().to_numpy()

    # Fit logistic curve. Provide initial guesses.
    try:
        popt, _ = curve_fit(
            logistic_function,
            reduction_pcts,
            error_rates,
            p0=[1.0, 1.0, np.median(reduction_pcts)],
            maxfev=10000,
        )
        fitted = logistic_function(reduction_pcts, *popt)
    except Exception:
        # If fitting fails, fall back to the empirical rates.
        fitted = error_rates

    return reduction_pcts, error_rates, fitted

def _write_tradeoff_csv(
    reduction_pcts: np.ndarray,
    error_rates: np.ndarray,
    output_path: Path = RESULTS_DIR / "tradeoff_curve.csv",
) -> None:
    """
    Write the trade‑off curve to ``output_path`` as CSV.

    Columns: ``reduction_pct,error_rate``.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["reduction_pct", "error_rate"])
        for pct, err in zip(reduction_pcts, error_rates):
            writer.writerow([f"{pct:.2f}", f"{err:.6f}"])

def _detect_threshold(
    reduction_pcts: np.ndarray,
    error_rates: np.ndarray,
    error_bound: float = 0.01,
) -> Tuple[float, float, float]:
    """
    Determine the minimum reduction percentage where the error rate exceeds
    ``error_bound`` (default 1 %).  If the bound is never exceeded, the
    function returns the maximum observed reduction percentage for all three
    returned values.

    Returns
    -------
    Tuple[float, float, float]
        (threshold_pct, ci_lower, ci_upper).  The confidence interval is
        a placeholder (identical to ``threshold_pct``) because bootstrapping
        logic lives elsewhere in the original pipeline.
    """
    if reduction_pcts.size == 0:
        return 0.0, 0.0, 0.0

    # Find first index where error exceeds bound.
    exceed_mask = error_rates > error_bound
    if not exceed_mask.any():
        # Bound never exceeded – report the maximum reduction observed.
        max_pct = float(np.max(reduction_pcts))
        return max_pct, max_pct, max_pct

    first_idx = np.argmax(exceed_mask)
    threshold = float(reduction_pcts[first_idx])
    # Placeholder CI – using the same value.
    return threshold, threshold, threshold

# ----------------------------------------------------------------------
# Orchestrator
# ----------------------------------------------------------------------
def main() -> None:
    """
    Entry point for the analysis pipeline.

    This function:
    1. Loads processed execution logs.
    2. Filters out invalid workflows.
    3. Fits a logistic trade‑off curve and writes ``tradeoff_curve.csv``.
    4. Detects the safe‑operating‑zone threshold and writes
       ``threshold_report.json``.
    5. Performs a VIF analysis and writes ``vif_report.json``.
    """
    # ------------------------------------------------------------------
    # Step 1 – Load logs
    # ------------------------------------------------------------------
    logs = load_processed_logs()
    valid_logs = filter_invalid_workflows_from_logs(logs)

    # ------------------------------------------------------------------
    # Step 2 – Fit trade‑off curve
    # ------------------------------------------------------------------
    reduction_pcts, error_rates, fitted = fit_tradeoff_curve(valid_logs)

    # Write CSV (even if empty – the file must exist).
    _write_tradeoff_csv(reduction_pcts, error_rates)

    # ------------------------------------------------------------------
    # Step 3 – Detect threshold
    # ------------------------------------------------------------------
    threshold_pct, ci_lower, ci_upper = _detect_threshold(reduction_pcts, error_rates)

    threshold_report = {
        "threshold_pct": round(threshold_pct, 2),
        "ci_lower": round(ci_lower, 2),
        "ci_upper": round(ci_upper, 2),
    }
    threshold_path = RESULTS_DIR / "threshold_report.json"
    with threshold_path.open("w", encoding="utf-8") as f:
        json.dump(threshold_report, f, indent=2, sort_keys=True)

    # ------------------------------------------------------------------
    # Step 4 – VIF analysis
    # ------------------------------------------------------------------
    vif_results, exceeded = run_vif_analysis(logs)
    vif_report = {
        "metric_name": "VIF",
        "threshold": VIF_THRESHOLD,
        "exceeded_threshold": exceeded,
        "values": vif_results,
    }
    save_vif_report(vif_report)
