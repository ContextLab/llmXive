"""Collinearity diagnostics (VIF) implementation for T024."""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path

import pandas as pd
import numpy as np
from statsmodels.stats.outliers_influence import variance_inflation_factor

from utils.logging import get_logger, log_operation


def setup_logger(name: str, log_file: str | None = None) -> logging.Logger:
    """Configure a logger for this module."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logger.addHandler(handler)

        if log_file:
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
            logger.addHandler(file_handler)

    return logger


def load_config(config_path: str = "code/config.yaml") -> dict:
    """Load configuration from YAML."""
    import yaml
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def load_analysis_results(
    complexity_file: str = "data/analysis/complexity_metrics.csv",
    delta_file: str = "data/analysis/delta_scores.csv"
) -> pd.DataFrame:
    """
    Load complexity metrics and delta scores, merge them, and prepare the predictor matrix.

    Returns a DataFrame with columns:
    - Fatigue_Delta
    - Pre_Complexity (median of LZC across channels for pre-state)
    - Available covariates (age, time_of_day, medication_status) if present.
    """
    logger = get_logger("collinearity")
    logger.info("Loading analysis results for VIF calculation.")

    if not os.path.exists(complexity_file):
        raise FileNotFoundError(f"Complexity metrics file not found: {complexity_file}")
    if not os.path.exists(delta_file):
        raise FileNotFoundError(f"Delta scores file not found: {delta_file}")

    complexity_df = pd.read_csv(complexity_file)
    delta_df = pd.read_csv(delta_file)

    # Ensure participant_id is string for merging
    complexity_df['participant_id'] = complexity_df['participant_id'].astype(str)
    delta_df['participant_id'] = delta_df['participant_id'].astype(str)

    # We need Pre_Complexity (LZC) for the pre-state.
    # Assuming complexity_metrics has a 'timepoint' or 'segment' column indicating pre/post.
    # If not, we assume the first segment is pre.
    # Based on T016 spec: "per channel per segment". T019 calculates deltas.
    # We need to aggregate complexity by participant and timepoint.

    # Filter for Pre state complexity (LZC)
    # Assumption: 'segment_id' or 'timepoint' indicates pre/post.
    # If 'timepoint' exists:
    if 'timepoint' in complexity_df.columns:
        pre_complexity = complexity_df[complexity_df['timepoint'] == 'pre']
    else:
        # Fallback: assume first segment per participant is pre, or aggregate all if no timepoint
        # For VIF, we need a single Pre_Complexity per participant.
        # Let's aggregate median LZC across channels for the 'pre' timepoint if available.
        # If 'timepoint' is missing, we might need to infer from 'segment_id' naming or just take all.
        # Given T019 calculates delta (Post - Pre), 'timepoint' should exist in delta_df.
        # We join delta_df to get the mapping, but we need Pre_Complexity.
        # Let's assume complexity_df has 'timepoint'. If not, we raise an error or aggregate.
        logger.warning("No 'timepoint' column in complexity_metrics.csv. Attempting to infer or aggregate.")
        pre_complexity = complexity_df # Fallback: use all if structure is flat

    # Aggregate Pre Complexity (median LZC per participant)
    # We assume 'lzc_value' is the column name from T016.
    if 'lzc_value' not in pre_complexity.columns:
        raise ValueError("Column 'lzc_value' not found in complexity_metrics.csv")

    pre_lzc = pre_complexity.groupby('participant_id')['lzc_value'].median().reset_index()
    pre_lzc.columns = ['participant_id', 'Pre_Complexity']

    # Prepare the main dataframe
    # Start with Fatigue_Delta from delta_df
    # T019 output: delta_scores.csv. Columns likely: participant_id, metric, delta_value (or similar).
    # T019 spec: "delta scores (Post - Pre) for both complexity and fatigue".
    # Let's assume delta_df has columns: participant_id, metric_name, delta_value.
    # We need Fatigue_Delta specifically.

    if 'metric' in delta_df.columns and 'delta_value' in delta_df.columns:
        fatigue_delta = delta_df[delta_df['metric'] == 'fatigue'][['participant_id', 'delta_value']]
        fatigue_delta.columns = ['participant_id', 'Fatigue_Delta']
    elif 'Fatigue_Delta' in delta_df.columns:
        fatigue_delta = delta_df[['participant_id', 'Fatigue_Delta']]
    else:
        # Try to find a column that looks like fatigue delta
        fatigue_cols = [c for c in delta_df.columns if 'fatigue' in c.lower() and 'delta' in c.lower()]
        if fatigue_cols:
            fatigue_delta = delta_df[['participant_id'] + fatigue_cols]
            fatigue_delta.columns = ['participant_id', 'Fatigue_Delta']
        else:
            raise ValueError("Could not identify Fatigue_Delta column in delta_scores.csv")

    # Merge
    df = pd.merge(pre_lzc, fatigue_delta, on='participant_id', how='inner')

    # Add covariates if they exist in delta_df (or a separate covariate file)
    # T024 spec: "covariates: age, time_of_day, medication_status"
    covariates = ['age', 'time_of_day', 'medication_status']
    for cov in covariates:
        if cov in delta_df.columns:
            # Merge covariates
            cov_df = delta_df[['participant_id', cov]].drop_duplicates()
            df = pd.merge(df, cov_df, on='participant_id', how='left')
            logger.info(f"Covariate '{cov}' found and merged.")
        else:
            logger.warning(f"Covariate '{cov}' not found in input data.")

    return df


def calculate_vif(df: pd.DataFrame, exclude: list | None = None) -> dict:
    """
    Calculate Variance Inflation Factor for each predictor in the DataFrame.

    Args:
        df: DataFrame with predictors as columns.
        exclude: List of column names to exclude from VIF calculation.

    Returns:
        Dictionary mapping predictor names to VIF values.
    """
    if exclude is None:
        exclude = []

    # Select columns
    predictors = [col for col in df.columns if col not in exclude]

    # Check for NaNs
    if df[predictors].isnull().any().any():
        logger = get_logger("collinearity")
        logger.warning("NaN values found in predictors. Dropping rows with NaNs for VIF calculation.")
        df_clean = df[predictors].dropna()
    else:
        df_clean = df[predictors]

    if df_clean.shape[0] < df_clean.shape[1] + 1:
        logger = get_logger("collinearity")
        logger.error("Not enough samples to calculate VIF (N < P + 1).")
        raise ValueError("Insufficient samples for VIF calculation.")

    # Add constant for intercept
    X = df_clean.values
    X = np.column_stack((np.ones(X.shape[0]), X))

    vif_data = {}
    for i, col in enumerate(predictors):
        # VIF for feature i is 1 / (1 - R^2_i)
        # where R^2_i is from regression of feature i on all other features.
        # statsmodels VIF function handles this.
        try:
            vif = variance_inflation_factor(X, i + 1) # +1 because index 0 is intercept
            vif_data[col] = vif
        except Exception as e:
            logger = get_logger("collinearity")
            logger.error(f"Error calculating VIF for {col}: {e}")
            vif_data[col] = np.nan

    return vif_data


def run_collinearity_diagnostics(
    config: dict,
    complexity_file: str = "data/analysis/complexity_metrics.csv",
    delta_file: str = "data/analysis/delta_scores.csv",
    log_file: str = "data/analysis/vif_diagnostics.log",
    output_json: str = "data/analysis/vif_valid_predictors.json"
) -> None:
    """
    Run VIF diagnostics, log results, and exit with code 1 if VIF >= 5.
    """
    logger = setup_logger("collinearity", log_file=log_file)
    logger.info("Starting collinearity diagnostics (VIF).")

    # Load data
    try:
        df = load_analysis_results(complexity_file, delta_file)
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)

    if df.empty:
        logger.error("No data available for VIF calculation.")
        sys.exit(1)

    logger.info(f"Data loaded. Shape: {df.shape}")
    logger.info(f"Columns: {list(df.columns)}")

    # Calculate VIF
    vif_results = calculate_vif(df)

    # Log all VIF values
    logger.info("VIF Results:")
    for predictor, vif_val in vif_results.items():
        logger.info(f"  {predictor}: {vif_val:.4f}")
        # Explicitly write to log file via logger (which is configured with FileHandler)

    # Check threshold
    threshold = 5.0
    collinear_predictors = []
    for predictor, vif_val in vif_results.items():
        if vif_val >= threshold:
            collinear_predictors.append(predictor)

    if collinear_predictors:
        logger.warning(f"Collinearity violation detected (VIF >= {threshold}):")
        for p in collinear_predictors:
            logger.warning(f"  - {p} (VIF: {vif_results[p]:.4f})")
        logger.error(f"Collinearity violation: VIF >= {threshold} for {collinear_predictors}. Study invalid per SC-004.")
        # HARD HALT
        sys.exit(1)
    else:
        logger.info(f"All predictors passed VIF check (threshold < {threshold}).")
        valid_predictors = list(vif_results.keys())

        # Write valid predictors to JSON
        os.makedirs(os.path.dirname(output_json), exist_ok=True)
        with open(output_json, 'w') as f:
            json.dump({"valid_predictors": valid_predictors}, f, indent=2)
        logger.info(f"Valid predictors written to {output_json}")


def save_collinearity_report(
    vif_results: dict,
    output_file: str = "data/analysis/vif_report.csv"
) -> None:
    """Save VIF results to a CSV file."""
    df = pd.DataFrame(list(vif_results.items()), columns=['predictor', 'vif'])
    df.to_csv(output_file, index=False)


def main():
    parser = argparse.ArgumentParser(description="Run collinearity diagnostics (VIF).")
    parser.add_argument("--config", default="code/config.yaml", help="Path to config file.")
    parser.add_argument("--complexity", default="data/analysis/complexity_metrics.csv", help="Path to complexity metrics.")
    parser.add_argument("--delta", default="data/analysis/delta_scores.csv", help="Path to delta scores.")
    parser.add_argument("--log", default="data/analysis/vif_diagnostics.log", help="Path to log file.")
    parser.add_argument("--output", default="data/analysis/vif_valid_predictors.json", help="Path to output JSON.")

    args = parser.parse_args()

    try:
        config = load_config(args.config)
    except Exception as e:
        print(f"Error loading config: {e}")
        sys.exit(1)

    run_collinearity_diagnostics(
        config=config,
        complexity_file=args.complexity,
        delta_file=args.delta,
        log_file=args.log,
        output_json=args.output
    )


if __name__ == "__main__":
    main()
