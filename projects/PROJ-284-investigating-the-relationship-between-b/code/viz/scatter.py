"""
Scatter plot generator for metric vs. score analysis.
Generates publication-quality plots with regression lines and statistical annotations.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

from code.logging_config import get_logger

logger = get_logger(__name__)

# Output directory for figures
FIGURE_DIR = Path("data/figures")
FIGURE_DIR.mkdir(parents=True, exist_ok=True)

def load_correlation_results() -> pd.DataFrame:
    """
    Load correlation results from data/analysis/correlations.csv.
    
    Returns:
        DataFrame with columns: metric_name, subject_id, value, fd, 
        correlation_r, correlation_p, fdr_q, significant
    """
    csv_path = Path("data/analysis/correlations.csv")
    if not csv_path.exists():
        logger.log("load_correlation_results_error", 
                  message=f"File not found: {csv_path}")
        raise FileNotFoundError(f"Correlation results file not found: {csv_path}")
    
    df = pd.read_csv(csv_path)
    logger.log("load_correlation_results_success", 
              record_count=len(df), 
              file=str(csv_path))
    return df

def generate_scatter_plot(
    metric_name: str,
    score_column: str = "motor_score",
    output_path: Optional[Union[str, Path]] = None,
    title: Optional[str] = None,
    x_label: Optional[str] = None,
    y_label: Optional[str] = None,
    figsize: tuple = (8, 6),
    dpi: int = 150
) -> str:
    """
    Generate a scatter plot of a network metric vs. behavioral score.
    
    Features:
    - Scatter points for each subject
    - Regression line with 95% confidence interval
    - Annotated r (correlation coefficient) and q (FDR-corrected p-value)
    - Significance threshold indication
    
    Args:
        metric_name: Name of the metric column in the correlation results
        score_column: Name of the behavioral score column (default: "motor_score")
        output_path: Path to save the plot. If None, uses data/figures/{metric_name}_scatter.png
        title: Custom title for the plot
        x_label: Custom x-axis label
        y_label: Custom y-axis label
        figsize: Figure size (width, height)
        dpi: Resolution for saved figure
        
    Returns:
        Path to the saved figure file
    """
    # Load data
    df = load_correlation_results()
    
    # Filter for the specific metric
    metric_df = df[df["metric_name"] == metric_name].copy()
    
    if len(metric_df) == 0:
        logger.log("generate_scatter_plot_warning",
                  message=f"No data found for metric: {metric_name}")
        # Create empty plot with warning
        fig, ax = plt.subplots(figsize=figsize)
        ax.text(0.5, 0.5, f"No data for {metric_name}", 
               transform=ax.transAxes, ha='center', va='center')
        ax.set_title("No Data Available")
        output_path = output_path or FIGURE_DIR / f"{metric_name}_scatter.png"
        plt.savefig(output_path, dpi=dpi, bbox_inches='tight')
        plt.close()
        return str(output_path)
    
    # Extract values
    x_values = metric_df[score_column].values
    y_values = metric_df[metric_name].values
    
    # Remove NaN values
    valid_mask = ~(np.isnan(x_values) | np.isnan(y_values))
    x_valid = x_values[valid_mask]
    y_valid = y_values[valid_mask]
    
    if len(x_valid) < 2:
        logger.log("generate_scatter_plot_warning",
                  message=f"Insufficient data points for {metric_name}")
        fig, ax = plt.subplots(figsize=figsize)
        ax.text(0.5, 0.5, "Insufficient data points", 
               transform=ax.transAxes, ha='center', va='center')
        output_path = output_path or FIGURE_DIR / f"{metric_name}_scatter.png"
        plt.savefig(output_path, dpi=dpi, bbox_inches='tight')
        plt.close()
        return str(output_path)
    
    # Calculate regression
    slope, intercept, r_value, p_value, std_err = stats.linregress(x_valid, y_valid)
    
    # Generate regression line points
    x_line = np.linspace(x_valid.min(), x_valid.max(), 100)
    y_line = slope * x_line + intercept
    
    # Calculate 95% confidence interval for regression
    # Using standard error of prediction
    x_mean = np.mean(x_valid)
    ss_x = np.sum((x_valid - x_mean) ** 2)
    se_pred = std_err * np.sqrt(1 + 1/len(x_valid) + (x_line - x_mean)**2 / ss_x)
    ci_upper = y_line + 1.96 * se_pred
    ci_lower = y_line - 1.96 * se_pred
    
    # Create plot
    fig, ax = plt.subplots(figsize=figsize)
    
    # Scatter plot
    ax.scatter(x_valid, y_valid, alpha=0.6, edgecolors='black', linewidth=0.5, 
              label='Subjects', color='#3498db')
    
    # Regression line
    ax.plot(x_line, y_line, 'r-', linewidth=2, label='Regression Line')
    
    # Confidence interval
    ax.fill_between(x_line, ci_lower, ci_upper, color='red', alpha=0.2, 
                   label='95% CI')
    
    # Calculate FDR-corrected q-value for this metric
    # Find the q-value from the dataframe
    q_val = metric_df['fdr_q'].iloc[0] if 'fdr_q' in metric_df.columns else None
    significant = metric_df['significant'].iloc[0] if 'significant' in metric_df.columns else (p_value < 0.05)
    
    # Annotation
    annotation = f"r = {r_value:.3f}\n"
    if q_val is not None:
        annotation += f"q (FDR) = {q_val:.3f}\n"
    else:
        annotation += f"p = {p_value:.3f}\n"
    annotation += f"n = {len(x_valid)}"
    
    if significant:
        annotation += "\n✓ Significant"
    
    ax.text(0.05, 0.95, annotation, transform=ax.transAxes, 
           verticalalignment='top', horizontalalignment='left',
           bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5),
           fontsize=10)
    
    # Labels and title
    if x_label is None:
        x_label = score_column.replace('_', ' ').title()
    if y_label is None:
        y_label = metric_name.replace('_', ' ').title()
    if title is None:
        title = f"{y_label} vs {x_label}"
    
    ax.set_xlabel(x_label, fontsize=12)
    ax.set_ylabel(y_label, fontsize=12)
    ax.set_title(title, fontsize=14, fontweight='bold')
    
    ax.legend(loc='best')
    ax.grid(True, alpha=0.3)
    
    # Save figure
    if output_path is None:
        output_path = FIGURE_DIR / f"{metric_name}_scatter.png"
    else:
        output_path = Path(output_path)
    
    plt.savefig(output_path, dpi=dpi, bbox_inches='tight')
    plt.close()
    
    logger.log("scatter_plot_generated",
              metric=metric_name,
              r_value=r_value,
              p_value=p_value,
              q_value=q_val,
              n=len(x_valid),
              output=str(output_path))
    
    return str(output_path)

def generate_all_scatter_plots(
    metrics: Optional[List[str]] = None,
    score_column: str = "motor_score"
) -> List[str]:
    """
    Generate scatter plots for all specified metrics.
    
    Args:
        metrics: List of metric names to plot. If None, uses all unique metrics
                from the correlation results.
        score_column: Behavioral score column to use for x-axis
        
    Returns:
        List of paths to generated figure files
    """
    df = load_correlation_results()
    
    if metrics is None:
        metrics = df['metric_name'].unique().tolist()
    
    output_paths = []
    for metric in metrics:
        try:
            path = generate_scatter_plot(
                metric_name=metric,
                score_column=score_column
            )
            output_paths.append(path)
        except Exception as e:
            logger.log("scatter_plot_error",
                      metric=metric,
                      error=str(e))
            # Continue with other metrics
            continue
    
    logger.log("all_scatter_plots_generated",
              count=len(output_paths),
              metrics=metrics)
    return output_paths

def main():
    """
    Main entry point for generating scatter plots.
    Can be run from command line or as a module.
    """
    logger.log("scatter_plot_main_start")
    
    try:
        # Generate plots for all available metrics
        plots = generate_all_scatter_plots()
        
        if plots:
            logger.log("scatter_plot_main_success",
                      plots_generated=len(plots),
                      plot_paths=plots)
            print(f"Generated {len(plots)} scatter plots in {FIGURE_DIR}")
            for p in plots:
                print(f"  - {p}")
        else:
            logger.log("scatter_plot_main_warning",
                      message="No plots were generated")
            print("No plots were generated. Check logs for details.")
            
    except Exception as e:
        logger.log("scatter_plot_main_error", error=str(e))
        print(f"Error generating scatter plots: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()