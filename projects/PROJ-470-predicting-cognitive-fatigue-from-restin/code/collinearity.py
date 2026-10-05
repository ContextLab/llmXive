"""
Collinearity diagnostics (VIF < 5) for US3 per SC-004.

Calculates Variance Inflation Factor (VIF) for all available predictors
(Fatigue_Delta, Pre_Complexity, and covariates: age, time_of_day, medication_status).
Writes diagnostics to data/analysis/vif_diagnostics.log and valid predictors to
data/analysis/vif_valid_predictors.json.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import List, Dict, Any

import pandas as pd
import numpy as np
from statsmodels.stats.outliers_influence import variance_inflation_factor

# Import from project utils
from utils.logging import get_logger, log_operation


def setup_logger(name: str, log_file: str | None = None) -> logging.Logger:
    """Configure a logger with file and console handlers."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    if not logger.handlers:
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        if log_file:
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            fh = logging.FileHandler(log_file)
            fh.setLevel(logging.DEBUG)
            fh.setFormatter(formatter)
            logger.addHandler(fh)

        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        ch.setFormatter(formatter)
        logger.addHandler(ch)

    return logger


def load_config(config_path: str = "code/config.yaml") -> Dict[str, Any]:
    """Load pipeline configuration."""
    import yaml
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def load_analysis_results(
    complexity_file: str = "data/analysis/complexity_metrics.csv",
    delta_file: str = "data/analysis/delta_scores.csv"
) -> pd.DataFrame:
    """
    Load and merge complexity metrics and delta scores to form the predictor matrix.

    Returns a DataFrame with columns:
    - Fatigue_Delta
    - Pre_Complexity (median across channels per participant)
    - Any available covariates (age, time_of_day, medication_status)
    """
    if not os.path.exists(complexity_file):
        raise FileNotFoundError(f"Complexity metrics file not found: {complexity_file}")
    if not os.path.exists(delta_file):
        raise FileNotFoundError(f"Delta scores file not found: {delta_file}")

    complexity_df = pd.read_csv(complexity_file)
    delta_df = pd.read_csv(delta_file)

    # Aggregate complexity to participant level (median across channels)
    participant_complexity = (
        complexity_df
        .groupby(['participant_id', 'segment_id'])[['lzc_value', 'pe_value']]
        .median()
        .reset_index()
    )

    # Merge with delta scores
    # We assume delta_df has participant_id, fatigue_delta, and potentially covariates
    merged = pd.merge(
        delta_df,
        participant_complexity,
        on='participant_id',
        how='inner'
    )

    # If segment_id is in complexity but not delta, we might need to align.
    # For VIF, we typically use one row per participant.
    # Let's assume delta_df is already per-participant (one row per participant).
    # If complexity has multiple segments, we take the mean/median per participant.
    participant_complexity_agg = (
        participant_complexity
        .groupby('participant_id')[['lzc_value', 'pe_value']]
        .median()
        .reset_index()
        .rename(columns={'lzc_value': 'Pre_Complexity'})
    )

    final_df = pd.merge(delta_df, participant_complexity_agg, on='participant_id', how='inner')

    # Ensure required columns exist
    required = ['Fatigue_Delta', 'Pre_Complexity']
    missing = [col for col in required if col not in final_df.columns]
    if missing:
        raise ValueError(f"Missing required columns in merged data: {missing}")

    return final_df


def calculate_vif(
    df: pd.DataFrame,
    predictors: List[str]
) -> Dict[str, float]:
    """
    Calculate VIF for a list of predictors in the DataFrame.

    Returns a dict mapping predictor name to its VIF value.
    """
    X = df[predictors].dropna()
    if X.shape[0] < len(predictors) + 1:
        raise ValueError("Not enough samples to calculate VIF for given predictors.")

    # Add constant for intercept
    X = sm.add_constant(X)
    vif_data = {}
    for i, col in enumerate(X.columns):
        if col == 'const':
            continue
        vif = variance_inflation_factor(X.values, i)
        vif_data[col] = vif

    return vif_data


def run_collinearity_diagnostics(
    df: pd.DataFrame,
    vif_threshold: float = 5.0,
    logger: logging.Logger | None = None
) -> Dict[str, Any]:
    """
    Run VIF diagnostics on the available predictors.

    Identifies available predictors (Fatigue_Delta, Pre_Complexity, and covariates).
    Calculates VIF for all.
    Logs all VIF values to vif_diagnostics.log.
    Writes valid predictors (VIF < threshold) to vif_valid_predictors.json.

    Does NOT exit on failure; logs warnings for high VIF.
    """
    if logger is None:
        logger = logging.getLogger(__name__)

    # Define potential predictors
    core_predictors = ['Fatigue_Delta', 'Pre_Complexity']
    covariates = ['age', 'time_of_day', 'medication_status']

    # Identify which are present
    available_predictors = [p for p in core_predictors if p in df.columns]
    available_covariates = [c for c in covariates if c in df.columns]

    all_predictors = available_predictors + available_covariates

    if not all_predictors:
        logger.warning("No predictors available for VIF calculation.")
        return {'valid_predictors': [], 'vif_values': {}, 'status': 'no_predictors'}

    if len(all_predictors) < 2:
        logger.warning("At least 2 predictors required for VIF calculation.")
        # If only one predictor, VIF is undefined (or 1.0 by definition), but statsmodels requires >1
        # We'll handle this gracefully
        return {'valid_predictors': all_predictors, 'vif_values': {p: 1.0 for p in all_predictors}, 'status': 'single_predictor'}

    # Drop rows with NaN in any predictor
    clean_df = df[all_predictors].dropna()

    if clean_df.shape[0] < len(all_predictors) + 1:
        logger.warning(f"Insufficient samples ({clean_df.shape[0]}) for VIF with {len(all_predictors)} predictors.")
        return {'valid_predictors': [], 'vif_values': {}, 'status': 'insufficient_samples'}

    # Calculate VIF
    try:
        import statsmodels.api as sm
        X = sm.add_constant(clean_df[all_predictors])
        vif_values = {}
        for i, col in enumerate(X.columns):
            if col == 'const':
                continue
            vif = variance_inflation_factor(X.values, i)
            vif_values[col] = float(vif)
    except Exception as e:
        logger.error(f"Error calculating VIF: {e}")
        return {'valid_predictors': [], 'vif_values': {}, 'status': 'calculation_error', 'error': str(e)}

    # Identify valid predictors
    valid_predictors = [p for p, v in vif_values.items() if v < vif_threshold]
    invalid_predictors = [p for p, v in vif_values.items() if v >= vif_threshold]

    # Log diagnostics
    logger.info(f"VIF Diagnostics - Threshold: {vif_threshold}")
    logger.info(f"Available predictors: {all_predictors}")
    for p, v in vif_values.items():
        status = "VALID" if v < vif_threshold else "HIGH_VIF"
        logger.info(f"  {p}: VIF = {v:.4f} [{status}]")

    if invalid_predictors:
        logger.warning(f"Predictors with VIF >= {vif_threshold}: {invalid_predictors}")
    else:
        logger.info(f"All predictors passed VIF < {vif_threshold} threshold.")

    return {
        'valid_predictors': valid_predictors,
        'vif_values': vif_values,
        'status': 'completed',
        'invalid_predictors': invalid_predictors
    }


def save_collinearity_report(
    results: Dict[str, Any],
    log_path: str = "data/analysis/vif_diagnostics.log",
    json_path: str = "data/analysis/vif_valid_predictors.json"
):
    """
    Write VIF diagnostics to log and valid predictors to JSON.

    Note: This function appends to the log file to preserve previous entries.
    """
    # Ensure directories exist
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    os.makedirs(os.path.dirname(json_path), exist_ok=True)

    # Write JSON
    with open(json_path, 'w') as f:
        json.dump({'valid_predictors': results.get('valid_predictors', [])}, f, indent=2)

    # The logging is handled by the logger passed to run_collinearity_diagnostics.
    # This function ensures the JSON is written.


def main():
    parser = argparse.ArgumentParser(description="Run collinearity diagnostics (VIF).")
    parser.add_argument("--config", default="code/config.yaml", help="Path to config file.")
    parser.add_argument("--complexity", default="data/analysis/complexity_metrics.csv", help="Path to complexity metrics.")
    parser.add_argument("--delta", default="data/analysis/delta_scores.csv", help="Path to delta scores.")
    parser.add_argument("--vif-threshold", type=float, default=5.0, help="VIF threshold for validity.")
    args = parser.parse_args()

    # Setup logger
    logger = setup_logger("collinearity", "data/analysis/vif_diagnostics.log")
    logger.info("Starting collinearity diagnostics.")

    try:
        # Load data
        df = load_analysis_results(args.complexity, args.delta)
        logger.info(f"Loaded {len(df)} participants for VIF analysis.")

        # Run diagnostics
        results = run_collinearity_diagnostics(df, args.vif_threshold, logger)

        # Save results
        save_collinearity_report(results)
        logger.info(f"VIF diagnostics complete. Valid predictors: {results.get('valid_predictors', [])}")

    except Exception as e:
        logger.error(f"Collinearity diagnostics failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
