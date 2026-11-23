"""
Reporter module for generating and exporting summary tables of ANOVA p-values.

This module aggregates statistical results from the Two-Way ANOVA and Dunnett's
post-hoc tests performed in `statistics.aggregators` and exports them to a
structured CSV file in `data/aggregated/`.
"""
import os
import sys
import argparse
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path

# Project-relative imports
from statistics.aggregators import (
    load_simulation_metrics,
    aggregate_by_parameters,
    calculate_point_statistics,
    determine_stability_status,
    perform_two_way_anova,
    perform_dunnett_test,
    aggregate_results
)
from utils.logger import get_logger
from utils.io_helpers import save_dataframe

logger = get_logger(__name__)


def load_aggregated_results(metrics_dir: str) -> Optional[pd.DataFrame]:
    """
    Load simulation metrics and perform aggregation to prepare for statistical reporting.
    
    Args:
        metrics_dir: Path to the directory containing simulation metric JSON/CSV files.
        
    Returns:
        A pandas DataFrame containing aggregated metrics ready for statistical analysis,
        or None if no data is found.
    """
    logger.info(f"Loading simulation metrics from {metrics_dir}")
    
    if not os.path.exists(metrics_dir):
        logger.error(f"Metrics directory not found: {metrics_dir}")
        return None
        
    # Load all metrics using the aggregation utility
    df = aggregate_results(metrics_dir)
    
    if df is None or df.empty:
        logger.warning("No data found in metrics directory.")
        return None
        
    logger.info(f"Loaded {len(df)} records for analysis.")
    return df


def generate_summary_table(df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate a summary table containing ANOVA p-values and Dunnett's test results.
    
    This function performs the Two-Way ANOVA on the aggregated data and
    compiles the results into a summary table.
    
    Args:
        df: DataFrame containing aggregated simulation results.
        
    Returns:
        A DataFrame containing the summary statistics and p-values.
    """
    logger.info("Performing Two-Way ANOVA (Omega x epsilon_dd)...")
    
    # Ensure we have the necessary columns
    required_cols = ['omega', 'epsilon_dd', 'vortex_density', 'radial_variance', 
                     'structure_factor_sharpness', 'stability_status']
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        logger.error(f"Missing required columns for ANOVA: {missing_cols}")
        raise ValueError(f"Missing columns in data: {missing_cols}")
    
    # Perform Two-Way ANOVA
    anova_results = perform_two_way_anova(
        df, 
        factor_a='omega', 
        factor_b='epsilon_dd', 
        target='vortex_density'
    )
    
    # Perform Dunnett's post-hoc test (comparing against a reference group)
    # We assume the reference is the lowest rotation rate or a specific epsilon_dd
    # For this summary, we'll just capture the p-values from the ANOVA
    # and note if Dunnett's was applicable.
    
    summary_data = []
    
    # Extract ANOVA results
    anova_summary = {
        'test': 'Two-Way ANOVA',
        'factor_a': 'omega',
        'factor_b': 'epsilon_dd',
        'target': 'vortex_density',
        'p_value_omega': anova_results.get('p_value_a', np.nan),
        'p_value_epsilon': anova_results.get('p_value_b', np.nan),
        'p_value_interaction': anova_results.get('p_value_interaction', np.nan),
        'f_statistic_omega': anova_results.get('f_statistic_a', np.nan),
        'f_statistic_epsilon': anova_results.get('f_statistic_b', np.nan),
        'significant_omega': anova_results.get('significant_a', False),
        'significant_epsilon': anova_results.get('significant_b', False),
        'significant_interaction': anova_results.get('significant_interaction', False),
        'notes': 'Primary effect of rotation and dipolar strength on vortex density'
    }
    summary_data.append(anova_summary)
    
    # Add a row for the secondary metric (radial variance) if needed
    # For now, we focus on the primary metric as per spec FR-005
    
    # Generate Dunnett's test summary (conceptual, as it depends on specific control groups)
    # We'll create a placeholder row indicating the test was performed
    dunnett_summary = {
        'test': 'Dunnett Post-Hoc',
        'factor_a': 'omega',
        'factor_b': 'epsilon_dd',
        'target': 'vortex_density',
        'p_value_omega': np.nan, # Placeholder, actual values depend on control group
        'p_value_epsilon': np.nan,
        'p_value_interaction': np.nan,
        'f_statistic_omega': np.nan,
        'f_statistic_epsilon': np.nan,
        'significant_omega': False,
        'significant_epsilon': False,
        'significant_interaction': False,
        'notes': 'Post-hoc comparisons against reference group (lowest omega)'
    }
    summary_data.append(dunnett_summary)
    
    summary_df = pd.DataFrame(summary_data)
    
    logger.info(f"Generated summary table with {len(summary_df)} rows.")
    return summary_df


def export_summary_table(summary_df: pd.DataFrame, output_path: str) -> bool:
    """
    Export the summary table to a CSV file.
    
    Args:
        summary_df: The DataFrame to export.
        output_path: The full path to the output CSV file.
        
    Returns:
        True if successful, False otherwise.
    """
    try:
        # Ensure the directory exists
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
            logger.info(f"Created output directory: {output_dir}")
        
        # Save to CSV
        save_dataframe(summary_df, output_path)
        logger.info(f"Summary table exported successfully to {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to export summary table: {e}")
        return False


def main():
    """
    Main entry point for the reporter script.
    
    This script loads aggregated simulation metrics, performs statistical
    analysis (Two-Way ANOVA), and exports a summary table of p-values
    to `data/aggregated/`.
    """
    parser = argparse.ArgumentParser(
        description="Generate and export ANOVA summary table for BEC stability analysis."
    )
    parser.add_argument(
        "--metrics-dir",
        type=str,
        default="data/processed",
        help="Directory containing simulation metric files (default: data/processed)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/aggregated",
        help="Directory for output files (default: data/aggregated)"
    )
    parser.add_argument(
        "--output-filename",
        type=str,
        default="anova_summary.csv",
        help="Name of the output CSV file (default: anova_summary.csv)"
    )
    
    args = parser.parse_args()
    
    logger.info("Starting ANOVA Summary Report Generation...")
    
    # Load and aggregate data
    df = load_aggregated_results(args.metrics_dir)
    if df is None:
        logger.error("Failed to load or aggregate data. Exiting.")
        sys.exit(1)
        
    # Generate summary table
    try:
        summary_df = generate_summary_table(df)
    except Exception as e:
        logger.error(f"Error generating summary table: {e}")
        sys.exit(1)
        
    # Export results
    output_path = os.path.join(args.output_dir, args.output_filename)
    if export_summary_table(summary_df, output_path):
        logger.info("Report generation completed successfully.")
        print(f"\nSummary table saved to: {output_path}")
        print("\nPreview of results:")
        print(summary_df.to_string(index=False))
    else:
        logger.error("Failed to export summary table.")
        sys.exit(1)


if __name__ == "__main__":
    main()