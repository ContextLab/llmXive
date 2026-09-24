from __future__ import annotations
import argparse
import json
import logging
import os
import sys
import pandas as pd
import statsmodels.formula.api as sm
from pathlib import Path
from utils.logging import get_logger

def load_config(config_path: str) -> dict:
    """Loads pipeline configuration from a YAML file."""
    with open(config_path, "r") as f:
        return yaml.safe_load(f)

def validate_inputs(data_dir: str) -> None:
    """Validates the existence of required input files."""
    required_files = [
        Path(data_dir) / "cleaned_eeg.fif",
        Path(data_dir) / "complexity_metrics.csv",
        Path(data_dir) / "fatigue_scores.csv",
    ]
    for file in required_files:
        if not file.exists():
            raise FileNotFoundError(f"Required file not found: {file}")

def calculate_deltas(
    complexity_metrics_path: str, fatigue_scores_path: str
) -> pd.DataFrame:
    """Calculates delta scores for complexity and fatigue."""
    complexity_df = pd.read_csv(complexity_metrics_path)
    fatigue_df = pd.read_csv(fatigue_scores_path)

    # Ensure data is paired by participant_id
    merged_df = pd.merge(
        complexity_df,
        fatigue_df,
        on="participant_id",
        suffixes=("_complexity", "_fatigue"),
    )

    # Calculate delta scores
    merged_df["complexity_delta"] = (
        merged_df["lzc_value"] - merged_df["lzc_value"]
    )  # Placeholder - assuming pre/post are not in the csv
    merged_df["fatigue_delta"] = (
        merged_df["fatigue_rating"] - merged_df["fatigue_rating"]
    )  # Placeholder - assuming pre/post are not in the csv

    return merged_df

def compute_correlations(delta_scores_path: str) -> pd.DataFrame:
    """Computes Pearson correlation between delta scores."""
    delta_df = pd.read_csv(delta_scores_path)
    correlation = delta_df["complexity_delta"].corr(
        delta_df["fatigue_delta"]
    )
    return pd.DataFrame({"correlation": [correlation]})

def main():
    logger = get_logger("analysis")
    config_path = "code/config.yaml"
    data_dir = "data/processed"  # Assuming data is in data/processed
    analysis_dir = "data/analysis"

    try:
        validate_inputs(data_dir)
    except FileNotFoundError as e:
        logger.error(f"Missing input file: {e}")
        sys.exit(1)

    delta_scores_df = calculate_deltas(
        f"{data_dir}/complexity_metrics.csv",
        f"{data_dir}/fatigue_scores.csv",
    )
    correlation_df = compute_correlations(
        f"{analysis_dir}/delta_scores.csv"
    )

    # Save results
    delta_scores_df.to_csv(f"{analysis_dir}/delta_scores.csv", index=False)
    correlation_df.to_csv(f"{analysis_dir}/correlation_results.csv", index=False)

    logger.info("Analysis completed successfully.")

if __name__ == "__main__":
    import yaml
    main()