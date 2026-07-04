"""
Aggregator for final results and Pareto frontier generation.

This module orchestrates the generation of the final aggregated CSV
and the final Pareto frontier plot by combining latency data from
the executor and stability metrics from the stability analysis.
"""
import os
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional

# Import from existing API surface
from analysis.viz import load_stability_metrics, plot_pareto_frontier
from analysis.stats import load_latency_data

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def aggregate_results(
    latency_data_path: str,
    stability_metrics_path: str,
    output_csv_path: str
) -> pd.DataFrame:
    """
    Aggregate latency and stability data into a single CSV file.
    
    Args:
        latency_data_path: Path to the latency data JSONL/CSV
        stability_metrics_path: Path to the stability metrics CSV
        output_csv_path: Path for the output aggregated CSV
        
    Returns:
        DataFrame containing the aggregated results
    """
    logger.info(f"Loading latency data from {latency_data_path}")
    latency_df = load_latency_data(latency_data_path)
    
    logger.info(f"Loading stability metrics from {stability_metrics_path}")
    stability_df = load_stability_metrics(stability_metrics_path)
    
    if latency_df is None or stability_df is None:
        logger.error("Failed to load required data files")
        return pd.DataFrame()
    
    # Ensure we have common columns for merging
    # Expected columns in latency_df: config_id, kernel_type, median, p95, iterations
    # Expected columns in stability_df: config_id, kernel_type, l2_error, max_diff, status
    
    # Merge on config_id and kernel_type
    merged_df = pd.merge(
        latency_df,
        stability_df,
        on=['config_id', 'kernel_type'],
        how='inner'
    )
    
    if merged_df.empty:
        logger.warning("No matching records found after merging latency and stability data")
        return pd.DataFrame()
    
    # Ensure numerical columns are correct type
    numeric_cols = ['median', 'p95', 'l2_error', 'max_diff']
    for col in numeric_cols:
        if col in merged_df.columns:
            merged_df[col] = pd.to_numeric(merged_df[col], errors='coerce')
    
    # Filter out rows with NaN in critical columns for aggregation
    # We keep rows for the final CSV even if they have errors, 
    # but the Pareto plot logic will handle filtering
    logger.info(f"Aggregated {len(merged_df)} records")
    
    # Save to CSV
    output_path = Path(output_csv_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    merged_df.to_csv(output_csv_path, index=False)
    logger.info(f"Saved aggregated results to {output_csv_path}")
    
    return merged_df

def generate_final_pareto(
    aggregated_csv_path: str,
    output_plot_path: str,
    error_threshold: float = 1e-5
) -> None:
    """
    Generate the final Pareto frontier plot excluding unstable configurations.
    
    Args:
        aggregated_csv_path: Path to the aggregated CSV file
        output_plot_path: Path for the output PNG plot
        error_threshold: Maximum allowed error for inclusion in final plot
    """
    logger.info(f"Generating final Pareto frontier from {aggregated_csv_path}")
    
    df = pd.read_csv(aggregated_csv_path)
    
    if df.empty:
        logger.error("Aggregated CSV is empty, cannot generate plot")
        return
    
    # Filter for stable configurations (error <= threshold)
    # According to T031 and Constitution Principle VI
    stable_df = df[df['max_diff'] <= error_threshold].copy()
    
    if stable_df.empty:
        logger.warning("No stable configurations found for final Pareto plot")
        # Still generate an empty plot or a placeholder
        # But ideally we should have data
    else:
        logger.info(f"Found {len(stable_df)} stable configurations for final Pareto plot")
    
    # Generate the plot using the existing viz module
    # plot_pareto_frontier expects a DataFrame and output path
    plot_pareto_frontier(
        df=stable_df,
        x_col='median',
        y_col='max_diff',
        output_path=output_plot_path,
        title='Final Pareto Frontier (Stable Configurations Only)',
        xlabel='Median Latency (s)',
        ylabel='Max Absolute Difference'
    )
    
    logger.info(f"Saved final Pareto frontier plot to {output_plot_path}")

def main():
    """
    Main entry point for T032: Generate final aggregated.csv and pareto_frontier_final.png
    """
    # Define paths based on project structure
    base_dir = Path(__file__).parent.parent.parent
    latency_path = base_dir / "data" / "intermediates" / "raw_logs"
    stability_path = base_dir / "data" / "results" / "stability_metrics.csv"
    aggregated_output = base_dir / "data" / "results" / "aggregated.csv"
    pareto_output = base_dir / "data" / "results" / "pareto_frontier_final.png"
    
    # If raw_logs is a directory, we need to find the JSONL files
    # The load_latency_data function in stats.py handles directory input
    latency_input = str(latency_path) if latency_path.is_dir() else str(latency_path)
    
    # Step 1: Aggregate results
    aggregated_df = aggregate_results(
        latency_data_path=latency_input,
        stability_metrics_path=str(stability_path),
        output_csv_path=str(aggregated_output)
    )
    
    if aggregated_df.empty:
        logger.error("Aggregation failed. Cannot proceed to Pareto plot.")
        return 1
    
    # Step 2: Generate final Pareto frontier
    generate_final_pareto(
        aggregated_csv_path=str(aggregated_output),
        output_plot_path=str(pareto_output),
        error_threshold=1e-5
    )
    
    logger.info("T032 completed successfully.")
    return 0

if __name__ == "__main__":
    exit(main())
