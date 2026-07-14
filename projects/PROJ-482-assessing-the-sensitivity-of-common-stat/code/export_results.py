"""
Export results script to orchestrate the final export of aggregated data and plots.

This script depends on the analyzer for data processing and the visualizer for plotting.
"""
import os
import logging
from typing import Optional, List, Dict, Any
import pandas as pd
import numpy as np
from analyzer import load_simulation_results, aggregate_results, export_results_to_csv
from visualizer import generate_all_plots

logger = logging.getLogger(__name__)

def ensure_output_dirs():
    """Ensure all required output directories exist."""
    dirs = [
        'data/processed',
        'data/processed/plots'
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)
        logger.debug(f"Ensured directory: {d}")

def export_final_results(aggregated_df: pd.DataFrame, csv_path: str) -> None:
    """
    Export the final aggregated results to a CSV file.
    
    Args:
        aggregated_df: DataFrame with aggregated results.
        csv_path: Path to save the CSV file.
    """
    export_results_to_csv(aggregated_df, csv_path)
    logger.info(f"Final results exported to {csv_path}")

def save_plots(aggregated_df: pd.DataFrame, plot_dir: str) -> List[str]:
    """
    Generate and save all plots.
    
    Args:
        aggregated_df: DataFrame with aggregated results.
        plot_dir: Directory to save the plots.
        
    Returns:
        List of paths to generated plot files.
    """
    return generate_all_plots(aggregated_df, plot_dir)

def main():
    """
    Main entry point for the export script.
    Loads raw results, aggregates them, exports CSV, and generates plots.
    """
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    ensure_output_dirs()
    
    input_path = 'data/processed/raw_pvalues.csv'
    csv_output_path = 'data/processed/error_rates.csv'
    plot_output_dir = 'data/processed/plots'
    
    if not os.path.exists(input_path):
        logger.error(f"Input file not found: {input_path}")
        logger.error("Please run the simulation first.")
        return
    
    logger.info(f"Loading and aggregating results from {input_path}")
    raw_df = load_simulation_results(input_path)
    aggregated_df = aggregate_results(raw_df)
    
    logger.info(f"Exporting aggregated results to {csv_output_path}")
    export_final_results(aggregated_df, csv_output_path)
    
    logger.info(f"Generating plots in {plot_output_dir}")
    plot_files = save_plots(aggregated_df, plot_output_dir)
    
    logger.info(f"Export complete. Generated {len(plot_files)} plots.")

if __name__ == "__main__":
    main()
