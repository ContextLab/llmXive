"""Collinearity diagnostics for ANCOVA model predictors.

Implements SC-004: VIF < 5 for all predictors.
Calculates Variance Inflation Factor for Fatigue_Delta, Pre_Complexity,
and covariates (age, time_of_day, medication_status).
"""
from __future__ import annotations

import os
import sys
import json
import yaml
import logging
from pathlib import Path

import pandas as pd
import numpy as np
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.tools.tools import add_constant

# Import from sibling modules using exact names from API surface
from utils.logging import get_logger, log_operation


def load_config(config_path: str = "code/config.yaml") -> dict:
    """Load pipeline configuration."""
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def setup_logger(name: str, log_file: str | None = None) -> logging.Logger:
    """Set up a logger compatible with all callers.

    Supports:
      - get_logger("name")
      - get_logger(name, log_file)
      - get_logger(name, log_file="...")
      - get_logger() -> global
    """
    # Delegate to the tolerant logging module
    logger = get_logger(name, log_file)
    # Return a standard logging.Logger-like object for compatibility
    # The ReproducibilityLogger from utils.logging handles all calls
    return logger


def load_analysis_results(
    correlation_file: str = "data/analysis/correlation_results.csv",
    ancova_file: str = "data/analysis/ancova_results.csv",
    delta_file: str = "data/analysis/delta_scores.csv",
) -> pd.DataFrame:
    """Load and merge analysis results for VIF calculation.

    Expects:
      - delta_scores.csv with columns: participant_id, fatigue_delta, pre_complexity
      - ancova_results.csv or correlation_results.csv with covariates if available
    """
    # Load delta scores (primary source for predictors)
    if not os.path.exists(delta_file):
        raise FileNotFoundError(f"Delta scores file not found: {delta_file}")

    delta_df = pd.read_csv(delta_file)

    required_cols = ["participant_id", "fatigue_delta", "pre_complexity"]
    missing = [c for c in required_cols if c not in delta_df.columns]
    if missing:
        raise ValueError(f"Delta scores missing columns: {missing}")

    # Try to load covariates from a separate file if it exists
    covariates_file = "data/processed/covariates.csv"
    if os.path.exists(covariates_file):
        cov_df = pd.read_csv(covariates_file)
        required_cov = ["participant_id", "age", "time_of_day", "medication_status"]
        missing_cov = [c for c in required_cov if c not in cov_df.columns]
        if not missing_cov:
            # Merge covariates
            merged = delta_df.merge(cov_df, on="participant_id", how="inner")
            return merged
        else:
            # Log warning but continue without covariates
            logging.warning(f"Covariates file missing columns: {missing_cov}. Proceeding without covariates.")

    # If no covariates file, return just the core predictors
    return delta_df[["participant_id", "fatigue_delta", "pre_complexity"]]


def calculate_vif(df: pd.DataFrame, predictors: list[str]) -> dict[str, float]:
    """Calculate VIF for each predictor.

    Args:
        df: DataFrame with predictor columns
        predictors: List of column names to calculate VIF for

    Returns:
        Dict mapping predictor name to VIF value
    """
    if len(predictors) == 0:
        return {}

    # Add constant for intercept
    X = df[predictors].dropna()
    if X.empty:
        raise ValueError("No valid data rows after dropping NaNs")

    X_const = add_constant(X)

    vif_results = {}
    for i, col in enumerate(X_const.columns):
        if col == "const":
            continue
        try:
            vif_val = variance_inflation_factor(X_const.values, i)
            vif_results[col] = float(vif_val)
        except Exception as e:
            vif_results[col] = float('nan')
            logging.warning(f"Could not calculate VIF for {col}: {e}")

    return vif_results


def run_collinearity_diagnostics(
    predictors: list[str] | None = None,
    vif_threshold: float = 5.0,
) -> tuple[dict[str, float], bool]:
    """Run full collinearity diagnostics.

    Args:
        predictors: List of predictor column names. If None, auto-detect from data.
        vif_threshold: Maximum allowed VIF (default 5.0 per SC-004)

    Returns:
        Tuple of (vif_dict, passed_check)
    """
    # Define default predictors based on ANCOVA model
    default_predictors = ["fatigue_delta", "pre_complexity"]

    # Check for covariates
    covariates = ["age", "time_of_day", "medication_status"]
    data = load_analysis_results()

    # Auto-detect available predictors
    available_cols = set(data.columns)
    if predictors is None:
        predictors = [c for c in default_predictors + covariates if c in available_cols]

    if len(predictors) < 2:
        raise ValueError(f"Need at least 2 predictors for VIF, found: {predictors}")

    # Calculate VIF
    vif_results = calculate_vif(data, predictors)

    # Check threshold
    failed = False
    for pred, vif_val in vif_results.items():
        if np.isnan(vif_val) or vif_val >= vif_threshold:
            failed = True
            logging.warning(f"VIF for {pred} is {vif_val:.2f} (>= {vif_threshold})")

    return vif_results, not failed


def save_collinearity_report(
    vif_results: dict[str, float],
    passed: bool,
    output_path: str = "data/analysis/vif_diagnostics.log",
) -> None:
    """Save VIF diagnostics to log file.

    Format: Plain text with VIF values and pass/fail status.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w") as f:
        f.write("=== Collinearity Diagnostics (VIF) ===\n")
        f.write(f"Threshold: 5.0\n")
        f.write(f"Status: {'PASSED' if passed else 'FAILED'}\n\n")
        f.write("VIF Values:\n")
        for predictor, vif_val in sorted(vif_results.items()):
            status = "OK" if not np.isnan(vif_val) and vif_val < 5.0 else "WARNING"
            f.write(f"  {predictor}: {vif_val:.4f} [{status}]\n")
        f.write("\n")
        if not passed:
            f.write("CRITICAL: One or more predictors have VIF >= 5.0.\n")
            f.write("This violates SC-004 and indicates severe multicollinearity.\n")


def main() -> None:
    """Main entry point for collinearity diagnostics."""
    log_operation("start_collinearity_diagnostics")

    # Load config
    config = load_config()
    vif_threshold = config.get("vif_threshold", 5.0)

    # Set up logger
    logger = setup_logger("collinearity")

    try:
        # Run diagnostics
        vif_results, passed = run_collinearity_diagnostics(vif_threshold=vif_threshold)

        # Save report
        save_collinearity_report(vif_results, passed)

        if not passed:
            logger.error("VIF check FAILED. Exiting with code 1.")
            sys.exit(1)
        else:
            logger.info("VIF check PASSED.")
            sys.exit(0)

    except Exception as e:
        logger.error(f"Collinearity diagnostics failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
