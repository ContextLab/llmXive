"""
Script to generate the correlation results CSV file.

This module orchestrates the loading of merged metrics, computation of
Spearman correlations, application of FDR correction, and the final
generation of `data/processed/correlation_results.csv`.
"""
import os
import logging
import pandas as pd
from pathlib import Path
from typing import Optional, List, Dict, Any

# Import from sibling modules as per API surface
from stats_engine import (
    load_and_merge_metrics,
    compute_spearman_correlations,
    apply_benjamini_hochberg_fdr,
    save_correlation_results
)
from logger import setup_logger

logger = setup_logger(__name__)

def main():
    """
    Main entry point to generate the correlation results CSV.

    1. Loads and merges metrics from raw/processed data.
    2. Computes Spearman correlations.
    3. Applies Benjamini-Hochberg FDR correction.
    4. Saves the final results to `data/processed/correlation_results.csv`.
    """
    logger.info("Starting correlation results generation (T034).")

    # Ensure output directory exists
    output_dir = Path("data/processed")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "correlation_results.csv"

    # Step 1: Load and merge metrics
    # This relies on T017 (raw_calibration.csv) and T025 (graph_metrics.csv)
    try:
        merged_df = load_and_merge_metrics()
        if merged_df is None or merged_df.empty:
            logger.error("Merged metrics dataframe is empty. Cannot proceed with correlation.")
            # In a real run, we might raise an error here, but for the pipeline
            # we log and exit to prevent generating an empty file if upstream failed.
            return
    except FileNotFoundError as e:
        logger.error(f"Required data files not found: {e}")
        return
    except Exception as e:
        logger.error(f"Failed to load and merge metrics: {e}")
        return

    logger.info(f"Loaded merged metrics with {len(merged_df)} rows.")

    # Step 2: Compute Spearman correlations
    # This produces a DataFrame with columns: metric_a, metric_b, rho, p_value
    try:
        corr_df = compute_spearman_correlations(merged_df)
        if corr_df is None or corr_df.empty:
            logger.warning("No correlations computed. Output file will be empty or skipped.")
            # Create empty file with headers if needed, or skip
            corr_df = pd.DataFrame(columns=["metric_a", "metric_b", "spearman_rho", "p_value"])
    except Exception as e:
        logger.error(f"Failed to compute correlations: {e}")
        return

    logger.info(f"Computed {len(corr_df)} correlation pairs.")

    # Step 3: Apply Benjamini-Hochberg FDR correction
    # This adds 'adj_p_value' and 'is_significant' columns
    try:
        results_df = apply_benjamini_hochberg_fdr(corr_df)
        if results_df is None:
            logger.error("FDR correction failed.")
            return
    except Exception as e:
        logger.error(f"Failed to apply FDR correction: {e}")
        return

    # Step 4: Ensure required columns exist and format
    required_columns = [
        "metric_a", "metric_b", "spearman_rho", "p_value",
        "adj_p_value", "is_significant", "is_excluded"
    ]

    # Ensure 'is_excluded' column exists (default False unless logic in stats_engine adds it)
    if "is_excluded" not in results_df.columns:
        results_df["is_excluded"] = False

    # Select and order columns as per spec
    final_df = results_df[required_columns]

    # Step 5: Save to CSV
    try:
        final_df.to_csv(output_path, index=False)
        logger.info(f"Successfully saved correlation results to {output_path}")
        logger.info(f"File contains {len(final_df)} rows.")
        
        # Verification logging
        if len(final_df) > 0:
            logger.info(f"Sample row: {final_df.iloc[0].to_dict()}")
        else:
            logger.warning("Output file is empty (0 rows).")
    except Exception as e:
        logger.error(f"Failed to save results to {output_path}: {e}")
        return

    logger.info("T034 completed successfully.")

if __name__ == "__main__":
    main()
