"""
Visualization module for Neural Correlates of Anticipatory Reward project.
Generates scatter plots of firing rate vs. reward magnitude with confidence intervals.
"""
import os
import sys
import logging
from pathlib import Path
from typing import Optional, Dict, Any

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg') # Ensure non-interactive backend for headless execution
import matplotlib.pyplot as plt
import seaborn as sns

from logging_config import get_logger

logger = get_logger(__name__)

def plot_firing_rate_vs_reward(
    df: pd.DataFrame,
    output_path: str,
    x_col: str = 'reward_magnitude',
    y_col: str = 'firing_rate',
    title: str = 'Firing Rate vs Reward Magnitude',
    xlabel: str = 'Reward Magnitude',
    ylabel: str = 'Firing Rate (spikes/s)',
    ci: int = 95
) -> str:
    """
    Generate a scatter plot with regression line and confidence interval.

    Args:
        df: DataFrame containing the data.
        output_path: Path to save the output image.
        x_col: Name of the column for x-axis.
        y_col: Name of the column for y-axis.
        title: Plot title.
        xlabel: X-axis label.
        ylabel: Y-axis label.
        ci: Confidence interval percentage for the regression line.

    Returns:
        Path to the saved image.
    """
    logger.info(f"Generating plot: {output_path}")
    
    # Validate input
    if not isinstance(df, pd.DataFrame):
        raise TypeError("df must be a pandas DataFrame")
    if x_col not in df.columns or y_col not in df.columns:
        raise ValueError(f"Columns {x_col} or {y_col} not found in DataFrame")

    # Ensure output directory exists
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Create plot
    plt.figure(figsize=(10, 7))
    sns.set_style("whitegrid")
    
    # Use regplot for scatter + regression line + CI
    # If data is categorical (integers), we might want to treat x as categorical, 
    # but regplot handles continuous. If strictly categorical, use stripplot + line.
    # Assuming continuous or ordinal reward magnitude as per typical analysis.
    sns.regplot(
        x=x_col, 
        y=y_col, 
        data=df, 
        ci=ci, 
        scatter_kws={'alpha': 0.6, 's': 60},
        line_kws={'color': 'red'}
    )
    
    plt.title(title, fontsize=14)
    plt.xlabel(xlabel, fontsize=12)
    plt.ylabel(ylabel, fontsize=12)
    
    # Save figure
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Plot saved to {output_path}")
    return str(output_path)

def generate_visualization_report(
    df: pd.DataFrame,
    output_dir: str,
    model_results: Optional[Dict[str, Any]] = None
) -> Dict[str, str]:
    """
    Generate a suite of visualization reports.

    Args:
        df: Processed data DataFrame.
        output_dir: Directory to save outputs.
        model_results: Optional dictionary with model coefficients, p-values, etc.

    Returns:
        Dictionary mapping report type to file path.
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    reports = {}
    
    # Main scatter plot
    plot_path = output_path / "firing_rate_vs_reward.png"
    plot_firing_rate_vs_reward(
        df, 
        str(plot_path),
        x_col='reward_magnitude',
        y_col='firing_rate',
        title='Firing Rate vs Reward Magnitude (with 95% CI)'
    )
    reports['scatter'] = str(plot_path)
    
    # Residuals plot if model results are provided
    if model_results and 'residuals' in model_results:
        residuals = model_results['residuals']
        plt.figure(figsize=(8, 6))
        plt.hist(residuals, bins=30, alpha=0.7, edgecolor='black')
        plt.title('Distribution of Residuals')
        plt.xlabel('Residual Value')
        plt.ylabel('Frequency')
        res_path = output_path / "residuals_histogram.png"
        plt.savefig(res_path, dpi=300, bbox_inches='tight')
        plt.close()
        reports['residuals'] = str(res_path)
        
    return reports

def main():
    """
    Main entry point for standalone execution.
    Loads data and generates the primary visualization.
    
    Expects a validated CSV at data/processed/validated_data.csv containing:
    - reward_magnitude
    - firing_rate
    
    Outputs:
    - data/figures/firing_rate_vs_reward.png
    """
    # Default paths
    data_path = Path("data/processed/validated_data.csv")
    output_path = Path("data/figures/firing_rate_vs_reward.png")
    
    # Check for command line arguments
    if len(sys.argv) > 1:
        data_path = Path(sys.argv[1])
    if len(sys.argv) > 2:
        output_path = Path(sys.argv[2])
        
    if not data_path.exists():
        logger.error(f"Input data file not found: {data_path}")
        logger.error("Please ensure the ingestion pipeline (T011-T016) has run successfully.")
        sys.exit(1)
        
    logger.info(f"Loading data from {data_path}")
    try:
        df = pd.read_csv(data_path)
    except Exception as e:
        logger.error(f"Failed to load CSV: {e}")
        sys.exit(1)
    
    # Verify required columns exist
    required_cols = ['reward_magnitude', 'firing_rate']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        logger.error(f"Missing required columns in input data: {missing}")
        logger.error(f"Expected columns: {required_cols}")
        sys.exit(1)

    logger.info(f"Generating visualization to {output_path}")
    plot_firing_rate_vs_reward(df, str(output_path))
    
    logger.info("Visualization complete.")

if __name__ == "__main__":
    main()