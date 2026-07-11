"""
Visualization module for the statistical robustness evaluation pipeline.

This module generates plots and summary tables to visualize the degradation
of statistical metrics (Type I error, CI coverage, effect size bias)
across different error rates and types.

Expected Outputs:
- results/plots/: PNG files for degradation curves.
- results/tables/: CSV files for summary tables.
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/visualize.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)


def load_config(config_path: str) -> Dict[str, Any]:
    """Load configuration from a YAML file."""
    path = Path(config_path)
    if not path.exists():
        logger.error(f"Configuration file not found: {config_path}")
        sys.exit(1)
    
    with open(path, 'r') as f:
        return yaml.safe_load(f)


def load_results(results_dir: str) -> pd.DataFrame:
    """
    Aggregate results from the results/aggregated_metrics.json file.
    
    Returns a DataFrame containing error_rate, error_type, metric_name, and metric_value.
    """
    agg_path = Path(results_dir) / "aggregated_metrics.json"
    
    if not agg_path.exists():
        logger.error(f"Aggregated results file not found: {agg_path}")
        sys.exit(1)

    with open(agg_path, 'r') as f:
        data = json.load(f)

    # Normalize nested JSON into a flat DataFrame
    records = []
    for entry in data:
        base = {
            'dataset_name': entry.get('dataset_name'),
            'error_type': entry.get('error_type'),
            'error_rate': entry.get('error_rate'),
            'statistical_test': entry.get('statistical_test')
        }
        
        # Extract metrics (Type I error, CI coverage, etc.)
        metrics = entry.get('metrics', {})
        for metric_name, value in metrics.items():
            records.append({**base, 'metric_name': metric_name, 'metric_value': value})
    
    df = pd.DataFrame(records)
    return df


def plot_type_i_error_curve(df: pd.DataFrame, output_dir: str) -> None:
    """
    Plot Error Rate vs. Type I Error degradation curves.
    
    Args:
        df: DataFrame with aggregated results.
        output_dir: Directory to save the plot.
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Filter for Type I error metric
    type_i_df = df[df['metric_name'] == 'type_i_error_rate'].copy()
    
    if type_i_df.empty:
        logger.warning("No Type I error data found to plot.")
        return

    plt.figure(figsize=(10, 6))
    sns.lineplot(
        data=type_i_df,
        x='error_rate',
        y='metric_value',
        hue='error_type',
        style='statistical_test',
        marker='o'
    )
    
    plt.title('Type I Error Rate vs. Error Rate')
    plt.xlabel('Error Rate')
    plt.ylabel('Empirical Type I Error Rate')
    plt.legend(title='Error Type / Test')
    plt.grid(True, alpha=0.3)
    
    filename = "type_i_error_degradation.png"
    plt.savefig(output_path / filename, dpi=300, bbox_inches='tight')
    logger.info(f"Saved Type I Error plot: {output_path / filename}")
    plt.close()


def plot_ci_coverage_curve(df: pd.DataFrame, output_dir: str) -> None:
    """
    Plot Error Rate vs. CI Coverage curves.
    
    Args:
        df: DataFrame with aggregated results.
        output_dir: Directory to save the plot.
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Filter for CI coverage metric
    ci_df = df[df['metric_name'] == 'ci_coverage_rate'].copy()
    
    if ci_df.empty:
        logger.warning("No CI coverage data found to plot.")
        return

    plt.figure(figsize=(10, 6))
    sns.lineplot(
        data=ci_df,
        x='error_rate',
        y='metric_value',
        hue='error_type',
        style='statistical_test',
        marker='s'
    )
    
    # Add a reference line for 95% coverage
    plt.axhline(y=0.95, color='r', linestyle='--', label='Nominal 95% Coverage')
    
    plt.title('CI Coverage Rate vs. Error Rate')
    plt.xlabel('Error Rate')
    plt.ylabel('CI Coverage Rate')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    filename = "ci_coverage_degradation.png"
    plt.savefig(output_path / filename, dpi=300, bbox_inches='tight')
    logger.info(f"Saved CI Coverage plot: {output_path / filename}")
    plt.close()


def generate_summary_table(df: pd.DataFrame, output_dir: str) -> None:
    """
    Generate a summary CSV table showing coverage failure rates across tests and error levels.
    
    Args:
        df: DataFrame with aggregated results.
        output_dir: Directory to save the table.
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Pivot to get a readable table: Rows = Test, Cols = Error Rate, Values = Failure Rate (1 - Coverage)
    ci_df = df[df['metric_name'] == 'ci_coverage_rate'].copy()
    
    if ci_df.empty:
        logger.warning("No CI coverage data found to generate summary table.")
        return

    # Calculate failure rate
    ci_df['failure_rate'] = 1.0 - ci_df['metric_value']
    
    # Pivot table
    # Group by statistical_test and error_rate, average the failure rate if multiple datasets
    pivot_df = ci_df.pivot_table(
        values='failure_rate',
        index='statistical_test',
        columns='error_rate',
        aggfunc='mean',
        fill_value=0.0
    )
    
    filename = "coverage_failure_summary.csv"
    pivot_df.to_csv(output_path / filename)
    logger.info(f"Saved Summary Table: {output_path / filename}")


def main():
    """
    Main entry point for the visualization pipeline.
    
    Usage:
        python code/visualize.py --config config/visualize.yaml --results results/
    """
    parser = argparse.ArgumentParser(description="Generate visualization artifacts for statistical robustness study.")
    parser.add_argument(
        "--config", 
        type=str, 
        default="config/visualize.yaml",
        help="Path to the visualization configuration file."
    )
    parser.add_argument(
        "--results", 
        type=str, 
        default="results",
        help="Path to the results directory containing aggregated_metrics.json."
    )
    parser.add_argument(
        "--output-plots", 
        type=str, 
        default="results/plots",
        help="Directory to save generated plots."
    )
    parser.add_argument(
        "--output-tables", 
        type=str, 
        default="results/tables",
        help="Directory to save generated tables."
    )
    
    args = parser.parse_args()
    
    logger.info("Starting visualization pipeline...")
    
    # Load config (optional, could be used to override paths or plot styles)
    try:
        config = load_config(args.config)
        logger.info(f"Loaded configuration from {args.config}")
    except Exception as e:
        logger.warning(f"Could not load config {args.config}: {e}. Using defaults.")
        config = {}
    
    # Load aggregated results
    df = load_results(args.results)
    logger.info(f"Loaded {len(df)} records from aggregated results.")
    
    # Generate Plots
    logger.info("Generating Type I Error degradation curve...")
    plot_type_i_error_curve(df, args.output_plots)
    
    logger.info("Generating CI Coverage degradation curve...")
    plot_ci_coverage_curve(df, args.output_plots)
    
    # Generate Tables
    logger.info("Generating summary table...")
    generate_summary_table(df, args.output_tables)
    
    logger.info("Visualization pipeline completed successfully.")


if __name__ == "__main__":
    main()