"""Sensitivity Analysis Module.

Implements FR-006: Sensitivity analysis at p≤0.05 and p≤0.01 thresholds.
Performs analysis on RAW p-values from correlation results.
"""
from __future__ import annotations

import os
import sys
import csv
from pathlib import Path

import pandas as pd
import numpy as np

# Import local project utilities
# Note: We assume utils.logging is available as per the API surface provided.
# We use a tolerant import pattern to avoid breaking if the module state is transient.
try:
    from utils.logging import get_logger, save_exclusion_log_csv
except ImportError:
    # Fallback for isolated execution if utils.logging is not in path
    # In the full pipeline, this import should succeed.
    import logging
    def get_logger(name, *args, **kwargs):
        return logging.getLogger(name)
    def save_exclusion_log_csv(*args, **kwargs):
        pass

def load_config():
    """Load configuration from code/config.yaml."""
    import yaml
    config_path = Path("code/config.yaml")
    if config_path.exists():
        with open(config_path, "r") as f:
            return yaml.safe_load(f)
    return {}

def load_analysis_results():
    """Load correlation results from data/analysis/correlation_results.csv.

    Returns:
        pd.DataFrame: The correlation results dataframe.

    Raises:
        FileNotFoundError: If the correlation results file is missing.
        ValueError: If the required columns are missing.
    """
    input_path = Path("data/analysis/correlation_results.csv")
    if not input_path.exists():
        raise FileNotFoundError(f"Correlation results file not found: {input_path}")

    df = pd.read_csv(input_path)

    required_cols = ["p_value", "channel"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in {input_path}: {missing}")

    # Ensure p_value is numeric and coerce errors to NaN (which we handle later)
    df["p_value"] = pd.to_numeric(df["p_value"], errors="coerce")

    return df

def run_sensitivity_analysis(df: pd.DataFrame, thresholds: list[float] = None) -> pd.DataFrame:
    """Run sensitivity analysis on raw p-values.

    Counts the number of electrodes (channels) with p < threshold for each threshold.

    Args:
        df: DataFrame containing 'p_value' and 'channel' columns.
        thresholds: List of p-value thresholds to analyze (default [0.05, 0.01]).

    Returns:
        pd.DataFrame: A summary table with columns:
            - threshold: The p-value threshold.
            - significant_count: Number of channels with p < threshold.
            - total_count: Total number of channels analyzed.
            - proportion: Ratio of significant channels.
    """
    if thresholds is None:
        thresholds = [0.05, 0.01]

    # Filter out NaN p-values to ensure accurate counting
    valid_df = df.dropna(subset=["p_value"])
    total_channels = len(valid_df)

    if total_channels == 0:
        # Handle edge case of no valid data
        return pd.DataFrame([
            {"threshold": t, "significant_count": 0, "total_count": 0, "proportion": 0.0}
            for t in thresholds
        ])

    results = []
    for t in thresholds:
        sig_count = (valid_df["p_value"] < t).sum()
        prop = sig_count / total_channels if total_channels > 0 else 0.0
        results.append({
            "threshold": t,
            "significant_count": int(sig_count),
            "total_count": int(total_channels),
            "proportion": float(prop)
        })

    return pd.DataFrame(results)

def generate_sensitivity_table(results_df: pd.DataFrame, output_path: Path):
    """Write the sensitivity analysis table to a CSV file.

    Args:
        results_df: The sensitivity analysis result dataframe.
        output_path: Path to the output CSV file.
    """
    # Ensure the directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write to CSV
    results_df.to_csv(output_path, index=False)

    logger = get_logger("sensitivity_analysis")
    if hasattr(logger, "log"):
        logger.log("generate_sensitivity_table", output=str(output_path), rows=len(results_df))
    else:
        logger.info(f"Generated sensitivity table: {output_path}")

def main():
    """Main entry point for the sensitivity analysis pipeline."""
    logger = get_logger("sensitivity_analysis", log_file="data/analysis/sensitivity_analysis.log")

    try:
        logger.log("start_sensitivity_analysis")

        # Load configuration (optional, but good practice)
        config = load_config()

        # Load correlation results (Raw p-values)
        logger.log("loading_correlation_results")
        try:
            corr_df = load_analysis_results()
        except FileNotFoundError as e:
            logger.log("error", message=str(e))
            print(f"ERROR: {e}")
            sys.exit(1)
        except ValueError as e:
            logger.log("error", message=str(e))
            print(f"ERROR: {e}")
            sys.exit(1)

        logger.log("running_sensitivity_analysis", input_rows=len(corr_df))

        # Run analysis
        sensitivity_df = run_sensitivity_analysis(corr_df)

        # Define output path
        output_path = Path("data/analysis/sensitivity_table.csv")

        # Generate output
        generate_sensitivity_table(sensitivity_df, output_path)

        logger.log("finish_sensitivity_analysis", output=str(output_path))
        print(f"Sensitivity analysis complete. Output: {output_path}")
        print(sensitivity_df.to_string(index=False))

    except Exception as e:
        logger.log("critical_error", message=str(e))
        print(f"CRITICAL ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()