import os
import sys
import json
import logging
import traceback
import random
from typing import Dict, Any, List, Tuple, Optional
import pandas as pd
import numpy as np

from src.utils import get_logger, write_csv, write_json, read_csv, read_json
from src.config import get_data_root, get_state_root

logger = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper: Load results from previous steps
# ----------------------------------------------------------------------

def load_model_results() -> pd.DataFrame:
    """Load the dimension metrics results from T016/T017."""
    data_root = get_data_root()
    # Assuming T017 or T016 produced a summary file, or we read from metrics output
    # For T028 specifically, we rely on T026's raw output, but we need to ensure
    # the pipeline can load intermediate results if needed.
    path = Path(data_root) / "dimension_metrics.csv" # Hypothetical intermediate
    if os.path.exists(path):
        return pd.read_csv(path)
    return pd.DataFrame()

def load_sensitivity_sweep_data() -> pd.DataFrame:
    """Load the raw sensitivity sweep data from T026."""
    data_root = get_data_root()
    path = Path(data_root) / "sensitivity_sweep_raw.csv"
    if not os.path.exists(path):
        raise FileNotFoundError(f"Missing T026 output: {path}")
    return pd.read_csv(path)

# ----------------------------------------------------------------------
# T027: Stability and Flip Rate Logic
# ----------------------------------------------------------------------

def calculate_stability_and_flip_rate(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate flip rate for each dimension across thresholds.
    Input: DataFrame with [dimension, threshold, status]
    Output: DataFrame with [dimension, threshold, status, flip_rate]
    """
    if df.empty:
        return df

    # Sort by dimension and threshold to ensure order
    df = df.sort_values(by=['dimension', 'threshold'])

    results = []
    dimensions = df['dimension'].unique()

    for dim in dimensions:
        dim_data = df[df['dimension'] == dim].sort_values('threshold')
        statuses = dim_data['status'].values
        thresholds = dim_data['threshold'].values

        # Calculate flip rate: number of changes / (N-1)
        # Or simply count transitions
        flips = 0
        for i in range(1, len(statuses)):
            if statuses[i] != statuses[i-1]:
                flips += 1

        # Flip rate as a proportion of possible transitions
        if len(statuses) > 1:
            flip_rate = flips / (len(statuses) - 1)
        else:
            flip_rate = 0.0

        for i, row in dim_data.iterrows():
            new_row = row.to_dict()
            new_row['flip_rate'] = flip_rate
            results.append(new_row)

    return pd.DataFrame(results)

def flag_threshold_sensitive(df: pd.DataFrame, flip_threshold: float = 0.5) -> pd.DataFrame:
    """
    Flag dimensions as 'threshold-sensitive' if flip_rate > threshold.
    """
    df['is_threshold_sensitive'] = df['flip_rate'] > flip_threshold
    return df

def generate_sensitivity_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """
    Full pipeline for T027: Calculate stability and flag sensitivity.
    """
    df = calculate_stability_and_flip_rate(df)
    df = flag_threshold_sensitive(df)
    return df

# ----------------------------------------------------------------------
# T028: Generate Full Sensitivity Matrix
# ----------------------------------------------------------------------

def generate_full_sensitivity_matrix(raw_df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate the full sensitivity matrix table for T028.
    
    This function ensures the output is a clean, complete table showing
    the classification outcome for EACH dimension at ALL tested thresholds.
    
    Input:
      raw_df: DataFrame from T026 with columns [dimension, threshold, status]
    
    Output:
      DataFrame with columns [dimension, threshold, status]
      Sorted by dimension and threshold for readability.
    """
    if raw_df.empty:
        logger.warning("Input DataFrame is empty. Returning empty matrix.")
        return pd.DataFrame(columns=['dimension', 'threshold', 'status'])

    # Ensure we have the required columns
    required_cols = ['dimension', 'threshold', 'status']
    missing_cols = [c for c in required_cols if c not in raw_df.columns]
    if missing_cols:
        raise ValueError(f"Input DataFrame missing required columns: {missing_cols}")

    # Clean and sort
    matrix_df = raw_df[required_cols].copy()
    matrix_df = matrix_df.sort_values(by=['dimension', 'threshold']).reset_index(drop=True)

    # Ensure status is a string (in case of mixed types)
    matrix_df['status'] = matrix_df['status'].astype(str)

    # Ensure threshold is numeric for sorting (if not already)
    if not pd.api.types.is_numeric_dtype(matrix_df['threshold']):
        matrix_df['threshold'] = pd.to_numeric(matrix_df['threshold'], errors='coerce')
        matrix_df = matrix_df.sort_values(by=['dimension', 'threshold'])

    return matrix_df

def main():
    """
    Main entry point for T028 execution if called directly.
    This script is primarily invoked via scripts/generate_sensitivity_matrix.py
    but providing a main here ensures consistency if needed.
    """
    logger.info("Starting T028: Generate Full Sensitivity Matrix")
    try:
        raw_df = load_sensitivity_sweep_data()
        matrix_df = generate_full_sensitivity_matrix(raw_df)
        
        output_path = Path(get_data_root()) / "sensitivity_matrix_full.csv"
        matrix_df.to_csv(output_path, index=False)
        logger.info(f"Successfully wrote {output_path}")
        return 0
    except Exception as e:
        logger.error(f"Error in T028: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
