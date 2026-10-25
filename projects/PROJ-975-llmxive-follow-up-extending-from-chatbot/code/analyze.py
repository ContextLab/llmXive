"""
Statistical analysis script for the llmXive follow‑up experiment.

This script loads the experiment CSV log, selects the HIGH‑overlap,
no‑pruning baseline, fits a single‑breakpoint piecewise linear regression
on binary success vs. library size, bootstraps the breakpoint estimate,
computes VIF for the orthogonalised predictors ``library_size`` and
``total_redundancy`` (derived from retrieval diversity), and writes the
results to ``data/results/analysis_report.json``.

The script is deliberately self‑contained and uses only the declared
project‑owned dependencies. It is invoked from the quickstart via:

    python code/analyze.py --input data/results/experiment_log.csv
"""
import argparse
import json
import logging
import os
from pathlib import Path

import numpy as np
import pandas as pd
import pwlf
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor

# Ensure output directory exists
Path("data/results").mkdir(parents=True, exist_ok=True)

logger = logging.getLogger(__name__)

def load_experiment_data(filepath: str = "data/results/experiment_log.csv") -> pd.DataFrame:
    """Load the experiment CSV log."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Experiment log not found at {filepath}")
    df = pd.read_csv(filepath)
    return df

def _extract_overlap(pruning_flag: str, run_id: str) -> str:
    """
    Helper to extract the overlap level from the ``run_id`` string.
    Expected format: ``run_<size>_<pruning>_<overlap>``.
    """
    parts = run_id.split("_")
    if len(parts) >= 4:
        return parts[3].upper()
    return ""

def filter_high_overlap_no_pruning(df: pd.DataFrame) -> pd.DataFrame:
    """
    Keep only rows that belong to the HIGH‑overlap condition and where
    pruning is disabled.
    """
    # ``pruning_enabled`` column is a boolean (True/False) written by the logger.
    # ``run_id`` encodes the overlap level.
    mask_pruning = df["pruning_enabled"] == False  # noqa: E712
    mask_overlap = df["run_id"].apply(_extract_overlap) == "HIGH"
    return df[mask_pruning & mask_overlap].copy()

def calculate_vif(df: pd.DataFrame, predictors: list) -> dict:
    """
    Calculate Variance Inflation Factor for each predictor in ``predictors``.
    Returns a mapping ``{predictor: vif_value}``.
    """
    X = df[predictors].astype(float)
    # Add constant term for VIF calculation
    X = sm.add_constant(X, has_constant='add')
    vif_dict = {}
    for i, col in enumerate(predictors, start=1):  # start=1 to skip constant at index 0
        vif = variance_inflation_factor(X.values, i)
        vif_dict[col] = float(vif)
    return vif_dict

def fit_piecewise_linear(df: pd.DataFrame) -> tuple:
    """
    Fit a single‑breakpoint piecewise linear model to binary success vs.
    library size using ``pwlf``.
    Returns ``(breakpoint, mse)``.
    """
    x = df["library_size"].values.astype(float)
    y = df["success"].astype(int).values.astype(float)

    # Ensure there is variability; pwlf requires at least two unique x values.
    if len(np.unique(x)) < 2:
        raise ValueError("Not enough distinct library sizes for regression.")

    # Two segments => one interior breakpoint
    pwlf_model = pwlf.PiecewiseLinFit(x, y)
    try:
        breaks = pwlf_model.fit(2)  # 2 segments
    except Exception as exc:
        raise RuntimeError(f"pwlf fitting failed: {exc}")

    # ``breaks`` includes the left and right bounds; interior breakpoint is at index 1
    breakpoint = breaks[1]
    # Compute mean squared error of the fitted model
    y_pred = pwlf_model.predict(x)
    mse = float(np.mean((y - y_pred) ** 2))
    return breakpoint, mse

def bootstrap_breakpoint(df: pd.DataFrame, n_boot: int = 1000, random_state: int = 42) -> dict:
    """
    Perform bootstrap resampling to obtain a 95 % confidence interval for the
    breakpoint estimate.
    Returns ``{'ci_lower': float, 'ci_upper': float, 'estimates': list}``.
    """
    rng = np.random.default_rng(random_state)
    estimates = []
    for _ in range(n_boot):
        sample = df.sample(frac=1.0, replace=True, random_state=rng.integers(0, 1_000_000))
        try:
            bp, _ = fit_piecewise_linear(sample)
            estimates.append(bp)
        except Exception:
            # In rare pathological resamples the fit may fail; skip those.
            continue
    if not estimates:
        raise RuntimeError("Bootstrap failed to produce any valid breakpoint estimates.")
    lower = float(np.percentile(estimates, 2.5))
    upper = float(np.percentile(estimates, 97.5))
    return {"ci_lower": lower, "ci_upper": upper, "estimates": estimates}

def run_analysis(input_path: str = "data/results/experiment_log.csv") -> dict:
    """
    Main analysis routine.

    Returns a dictionary that will be written to ``analysis_report.json``.
    The dictionary contains at least:
      - ``breakpoint_estimate`` (float)
      - ``breakpoint_ci`` (dict with ``lower`` and ``upper``)
      - ``vif_library_size`` (float)
      - ``vif_total_redundancy`` (float)
    """
    df = load_experiment_data(input_path)

    # Derive a simple proxy for total redundancy:
    # Higher ``retrieval_diversity`` means lower redundancy.
    # We define ``total_redundancy = 1 - retrieval_diversity``.
    if "retrieval_diversity" not in df.columns:
        raise KeyError("Column 'retrieval_diversity' missing from experiment log.")
    df["total_redundancy"] = 1.0 - df["retrieval_diversity"]

    # Filter to the baseline condition required by the specification.
    baseline_df = filter_high_overlap_no_pruning(df)

    if baseline_df.empty:
        raise ValueError("No rows found for HIGH overlap with pruning disabled.")

    # Piecewise linear regression
    breakpoint, mse = fit_piecewise_linear(baseline_df)

    # Bootstrap confidence interval
    boot = bootstrap_breakpoint(baseline_df, n_boot=1000)

    # VIF calculation
    vif_dict = calculate_vif(baseline_df, ["library_size", "total_redundancy"])

    report = {
        "breakpoint_estimate": float(breakpoint),
        "breakpoint_ci": {"lower": boot["ci_lower"], "upper": boot["ci_upper"]},
        "vif_library_size": vif_dict.get("library_size", None),
        "vif_total_redundancy": vif_dict.get("total_redundancy", None),
        "piecewise_mse": mse,
    }
    return report

def main():
    parser = argparse.ArgumentParser(description="Statistical analysis for llmXive follow‑up.")
    parser.add_argument(
        "--input",
        type=str,
        default="data/results/experiment_log.csv",
        help="Path to the experiment CSV log.",
    )
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    try:
        report = run_analysis(args.input)
        out_path = Path("data/results/analysis_report.json")
        with out_path.open("w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        logger.info(f"Analysis report written to {out_path}")
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise

if __name__ == "__main__":
    main()
