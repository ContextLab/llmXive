"""
Visualization module for generating scatter plots of network metrics vs. sensorimotor performance.

Task: T031 (Implementation of the function tested by T029)
Generates publication-quality scatter plots with regression lines and statistical annotations.
"""
import os
import logging
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for headless execution
import matplotlib.pyplot as plt
from pathlib import Path
from scipy import stats

from logging_config import get_logger

logger = get_logger(__name__)

def generate_scatter_plot(
    input_data: str,
    x_col: str,
    y_col: str,
    x_label: str,
    y_label: str,
    output_path: str,
    title: str = "Correlation Analysis"
) -> str:
    """
    Generate a scatter plot with regression line and statistical annotations.
    
    Args:
        input_data: Path to CSV file containing the data.
        x_col: Name of the column for the X-axis (network metric).
        y_col: Name of the column for the Y-axis (sensorimotor score).
        x_label: Label for the X-axis.
        y_label: Label for the Y-axis.
        output_path: Path where the PNG file will be saved.
        title: Title of the plot.
        
    Returns:
        Path to the generated PNG file.
        
    Raises:
        FileNotFoundError: If input CSV does not exist.
        ValueError: If specified columns are not found in the data.
    """
    input_path = Path(input_data)
    if not input_path.exists():
        raise FileNotFoundError(f"Input data file not found: {input_data}")
    
    df = pd.read_csv(input_data)
    
    # Validate columns
    required_cols = [x_col, y_col]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in input data: {missing_cols}")
    
    # Prepare data: Drop rows where either X or Y is NaN to ensure alignment
    valid_df = df[[x_col, y_col]].dropna()
    x = valid_df[x_col]
    y = valid_df[y_col]
    
    if len(x) < 3:
        logger.warning(f"Insufficient data points ({len(x)}) for regression analysis.")
        # Still generate plot but without regression line if too few points
        plot_regression = False
    else:
        plot_regression = True
    
    # Calculate statistics
    if plot_regression:
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
        r_squared = r_value ** 2
    else:
        slope = intercept = r_value = p_value = std_err = r_squared = np.nan
    
    # Create the plot
    plt.figure(figsize=(10, 8))
    plt.scatter(x, y, alpha=0.7, edgecolors='k', s=60, label='Subjects')
    
    if plot_regression:
        # Plot regression line
        x_line = np.linspace(x.min(), x.max(), 100)
        y_line = slope * x_line + intercept
        plt.plot(x_line, y_line, 'r-', linewidth=2, label=f'Regression (r={r_value:.3f})')
    
    # Annotations
    annotation_text = (
        f"n = {len(x)}\n"
        f"r = {r_value:.3f}\n"
        f"p = {p_value:.3g}"
    )
    
    plt.title(title, fontsize=16, fontweight='bold')
    plt.xlabel(x_label, fontsize=12)
    plt.ylabel(y_label, fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.legend(loc='best')
    
    # Add statistical text box
    plt.text(
        0.05, 0.95, annotation_text,
        transform=plt.gca().transAxes,
        fontsize=11,
        verticalalignment='top',
        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5)
    )
    
    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save the plot
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Scatter plot saved to: {output_path}")
    return str(output_path)

def main():
    """
    Entry point for command-line execution.
    Example usage:
    python code/viz/scatter.py --input data/analysis/full_metrics.csv --x col_x --y col_y --output figures/scatter.png
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate scatter plot of network metrics vs performance.")
    parser.add_argument("--input", required=True, help="Path to input CSV file.")
    parser.add_argument("--x", required=True, help="Column name for X-axis.")
    parser.add_argument("--y", required=True, help="Column name for Y-axis.")
    parser.add_argument("--x-label", default="Network Metric", help="Label for X-axis.")
    parser.add_argument("--y-label", default="Sensorimotor Performance", help="Label for Y-axis.")
    parser.add_argument("--output", required=True, help="Path to output PNG file.")
    parser.add_argument("--title", default="Correlation Analysis", help="Plot title.")
    
    args = parser.parse_args()
    
    from logging_config import setup_logging
    setup_logging()
    generate_scatter_plot(
        input_data=args.input,
        x_col=args.x,
        y_col=args.y,
        x_label=args.x_label,
        y_label=args.y_label,
        output_path=args.output,
        title=args.title
    )

if __name__ == "__main__":
    from logging_config import setup_logging
    setup_logging()
    main()