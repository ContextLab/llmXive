"""
Aggregator for Sensitivity Analysis Results (T032).

This module aggregates metrics from all sensitivity configurations
(bandwidths, window sizes, and tolerance sweeps) into a single
sensitivity.csv file as required by FR-007 and FR-010.

It assumes that:
1. T029 has generated metrics for different bandwidths/window sizes
   and stored them in a temporary structure or intermediate files.
2. T030 has generated tolerance sweep metrics.
3. The main.py entry point calls this aggregator after running the
   sensitivity grid and tolerance sweep.

Output:
- data/processed/sensitivity.csv: Aggregated metrics for all configurations.
"""

import os
import sys
import logging
import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Optional

# Import existing utilities if needed, though this is mostly data wrangling
# We rely on the outputs from T029 (grid) and T030 (tolerance)
# Since T029 and T030 are implemented, we assume they write to specific intermediate files
# or we can re-run the logic if needed. However, the most robust way is to assume
# the previous steps wrote their results to disk.

# Let's define the expected intermediate paths based on standard project conventions
# If T029 writes to data/processed/grid_results.csv and T030 writes to data/processed/tolerance_results.csv
# We will load, merge, and save to data/processed/sensitivity.csv

GRID_RESULTS_PATH = "data/processed/grid_results.csv"
TOLERANCE_RESULTS_PATH = "data/processed/tolerance_results.csv"
OUTPUT_PATH = "data/processed/sensitivity.csv"

# If these intermediate files don't exist, we might need to generate them on the fly
# if the previous tasks (T029, T030) didn't save them.
# However, T029 and T030 are marked as completed, so we assume they saved their outputs.
# If they didn't, we might need to re-run the logic here.
# To be safe, we will check for existence. If missing, we will try to reconstruct
# by calling the relevant functions from sensitivity.py if they expose a "run and return results" interface.
# But looking at the API surface for sensitivity.py:
# public names: run_tolerance_sweep, main
# It doesn't explicitly expose a "run_grid" function that returns data.
# T029 implementation likely wrote to a file.

# Let's implement the aggregator to load existing files.
# If files are missing, we log a warning and attempt to re-run the logic if possible,
# or raise an error.

logger = logging.getLogger(__name__)

def load_grid_results() -> Optional[pd.DataFrame]:
    """Load grid results from T029."""
    if os.path.exists(GRID_RESULTS_PATH):
        logger.info(f"Loading grid results from {GRID_RESULTS_PATH}")
        return pd.read_csv(GRID_RESULTS_PATH)
    else:
        logger.warning(f"Grid results file {GRID_RESULTS_PATH} not found.")
        return None

def load_tolerance_results() -> Optional[pd.DataFrame]:
    """Load tolerance results from T030."""
    if os.path.exists(TOLERANCE_RESULTS_PATH):
        logger.info(f"Loading tolerance results from {TOLERANCE_RESULTS_PATH}")
        return pd.read_csv(TOLERANCE_RESULTS_PATH)
    else:
        logger.warning(f"Tolerance results file {TOLERANCE_RESULTS_PATH} not found.")
        return None

def aggregate_metrics() -> pd.DataFrame:
    """
    Aggregate metrics from grid and tolerance sweeps into a single DataFrame.
    
    Returns:
        pd.DataFrame: Combined sensitivity analysis results.
    """
    grid_df = load_grid_results()
    tolerance_df = load_tolerance_results()
    
    if grid_df is None and tolerance_df is None:
        raise FileNotFoundError(
            "No sensitivity results found. Ensure T029 and T030 have been executed "
            "and their output files (grid_results.csv, tolerance_results.csv) exist."
        )
    
    results = []
    
    if grid_df is not None:
        # Ensure grid_df has the necessary columns
        # Expected columns from T029: bandwidth, window_size, precision, recall, f1_score, detection_delay
        # We might need to add a 'type' column to distinguish grid vs tolerance
        grid_df['analysis_type'] = 'grid'
        results.append(grid_df)
    
    if tolerance_df is not None:
        # Expected columns from T030: tolerance, precision, recall, f1_score, detection_delay
        # We might need to add a 'type' column and potentially standardize column names
        tolerance_df['analysis_type'] = 'tolerance'
        # If tolerance_df doesn't have bandwidth or window_size, we can set them to NaN or 'default'
        if 'bandwidth' not in tolerance_df.columns:
            tolerance_df['bandwidth'] = np.nan
        if 'window_size' not in tolerance_df.columns:
            tolerance_df['window_size'] = np.nan
        results.append(tolerance_df)
    
    if not results:
        raise ValueError("No data to aggregate.")
    
    combined_df = pd.concat(results, ignore_index=True)
    
    # Sort by analysis_type, then by relevant parameters
    combined_df = combined_df.sort_values(by=['analysis_type', 'bandwidth', 'window_size', 'tolerance'])
    
    return combined_df

def save_aggregated_metrics(df: pd.DataFrame, output_path: str):
    """
    Save the aggregated metrics to a CSV file.
    
    Args:
        df: DataFrame containing aggregated metrics.
        output_path: Path to save the CSV file.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Aggregated sensitivity metrics saved to {output_path}")

def main():
    """Main entry point for the sensitivity aggregator."""
    # Setup logging if not already done
    if not logging.root.handlers:
        from logging_setup import setup_logging
        setup_logging()
    
    logger.info("Starting sensitivity metrics aggregation (T032).")
    
    try:
        combined_df = aggregate_metrics()
        save_aggregated_metrics(combined_df, OUTPUT_PATH)
        logger.info("Sensitivity aggregation completed successfully.")
    except Exception as e:
        logger.error(f"Failed to aggregate sensitivity metrics: {e}")
        raise

if __name__ == "__main__":
    main()
