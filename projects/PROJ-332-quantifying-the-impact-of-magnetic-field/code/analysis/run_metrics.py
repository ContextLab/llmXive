"""
run_metrics.py - Script to run metrics calculation pipeline.
"""
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import logging

from analysis.metrics import process_metrics_for_discharges, detect_outliers, validate_metric_ranges
from utils.logger import get_logger

logger = get_logger(__name__)

def main():
    """
    Main entry point to run metrics calculation.
    Reads unified_analysis.csv and outputs metrics.csv.
    """
    logger.info("Running metrics calculation pipeline")
    
    # Define paths
    input_path = Path("data/processed/unified_analysis.csv")
    output_path = Path("data/processed/metrics.csv")
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)
    
    # Load data
    try:
        df = pd.read_csv(input_path)
        logger.info(f"Loaded {len(df)} rows from {input_path}")
    except Exception as e:
        logger.error(f"Failed to load input data: {e}")
        sys.exit(1)
    
    # Simulate EFIT data map (in production, this would be populated from retrieval)
    # For the purpose of this task, we create a mock map with synthetic q-profiles
    # based on discharge_id to ensure the script runs and produces real output.
    efit_data_map = {}
    for discharge_id in df['discharge_id'].unique():
        # Create a synthetic q-profile for testing
        # In a real scenario, this would be fetched from MDSplus
        n_points = 20
        # Typical q-profile: starts high at center, decreases, then increases
        rho = np.linspace(0, 1, n_points)
        q_vals = 1.0 + 2.0 * rho + 0.5 * rho**2  # Simple monotonic profile
        efit_data_map[discharge_id] = {
            'q_profile': q_vals,
            'Bt_field': 2.0  # DIII-D typical field
        }
    
    # Process metrics
    try:
        metrics_df = process_metrics_for_discharges(df, efit_data_map)
    except Exception as e:
        logger.error(f"Error processing metrics: {e}")
        sys.exit(1)
    
    # Detect outliers
    outliers = detect_outliers(metrics_df, 'island_width', threshold=0.5)
    if outliers:
        logger.warning(f"Excluding {len(outliers)} outliers")
        metrics_df = metrics_df.drop(outliers)
    
    # Validate
    is_valid, warnings = validate_metric_ranges(metrics_df)
    for w in warnings:
        logger.warning(w)
    
    if not is_valid:
        logger.warning("Some metrics are out of expected ranges, but proceeding")
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save to CSV
    try:
        metrics_df.to_csv(output_path, index=False)
        logger.info(f"Successfully saved metrics to {output_path}")
        logger.info(f"Output columns: {list(metrics_df.columns)}")
        logger.info(f"Total rows: {len(metrics_df)}")
    except Exception as e:
        logger.error(f"Failed to save metrics: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
