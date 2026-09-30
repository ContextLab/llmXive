"""
Script to generate the correlation results CSV file.

This script loads the processed performance and graph metrics, computes
Spearman correlations, applies FDR correction, and writes the final
results to data/processed/correlation_results.csv.
"""
import os
import logging
import pandas as pd
from pathlib import Path
from typing import Optional, List, Dict, Any

# Import from local modules
from stats_engine import (
    load_and_merge_metrics,
    compute_spearman_correlations,
    apply_benjamini_hochberg_fdr,
    save_correlation_results
)
from logger import setup_logger

# Setup logging
logger = setup_logger(__name__)

def main():
    """
    Main entry point for generating correlation results.
    
    This function:
    1. Loads and merges performance and graph metrics
    2. Computes Spearman correlations between all metric pairs
    3. Applies Benjamini-Hochberg FDR correction
    4. Saves the results to data/processed/correlation_results.csv
    """
    logger.info("Starting correlation results generation...")
    
    # Define output path
    output_path = Path("data/processed/correlation_results.csv")
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Check if input files exist
    perf_metrics_path = Path("data/processed/performance_metrics.csv")
    graph_metrics_path = Path("data/processed/graph_metrics.csv")
    
    if not perf_metrics_path.exists():
        logger.error(f"Performance metrics file not found: {perf_metrics_path}")
        logger.error("Please run the pipeline to generate performance_metrics.csv first.")
        raise FileNotFoundError(f"Missing required input file: {perf_metrics_path}")
    
    if not graph_metrics_path.exists():
        logger.error(f"Graph metrics file not found: {graph_metrics_path}")
        logger.error("Please run the pipeline to generate graph_metrics.csv first.")
        raise FileNotFoundError(f"Missing required input file: {graph_metrics_path}")
    
    try:
        # Load and merge metrics
        logger.info("Loading and merging metrics...")
        merged_df = load_and_merge_metrics()
        
        if merged_df is None or merged_df.empty:
            logger.error("No data available for correlation analysis after merging.")
            logger.error("Check that both input files contain valid data with matching device_ids.")
            raise ValueError("No valid data for correlation analysis")
        
        logger.info(f"Merged dataset contains {len(merged_df)} devices")
        
        # Compute correlations
        logger.info("Computing Spearman correlations...")
        correlations = compute_spearman_correlations(merged_df)
        
        if not correlations:
            logger.warning("No correlations computed. Check that there are numeric metrics in both datasets.")
            # Create empty result file with headers
            empty_df = pd.DataFrame(columns=["metric_a", "metric_b", "rho", "p_value", "adj_p_value"])
            empty_df.to_csv(output_path, index=False)
            logger.info(f"Created empty correlation results file: {output_path}")
            return
        
        # Apply FDR correction
        logger.info("Applying Benjamini-Hochberg FDR correction...")
        corrected_correlations = apply_benjamini_hochberg_fdr(correlations)
        
        # Save results
        logger.info(f"Saving correlation results to {output_path}...")
        save_correlation_results(corrected_correlations, output_path)
        
        logger.info("Correlation results generation completed successfully.")
        
        # Print summary
        significant_count = sum(1 for corr in corrected_correlations if corr['adj_p_value'] < 0.05)
        logger.info(f"Total correlations: {len(corrected_correlations)}")
        logger.info(f"Significant correlations (adj_p < 0.05): {significant_count}")
        
    except Exception as e:
        logger.error(f"Error during correlation results generation: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    main()