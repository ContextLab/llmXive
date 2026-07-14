"""
Visualization module for scatter plots.
Implements T031.
"""
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from scipy import stats

# Project imports
from code.logging_config import get_logger

logger = get_logger(__name__)

def generate_scatter_plot(
    data: pd.DataFrame,
    x_col: str,
    y_col: str,
    output_path: str,
    title: str = "Correlation Plot",
    xlabel: str = "Metric",
    ylabel: str = "Behavior",
    **kwargs
):
    """
    Generates a scatter plot with regression line and annotated r/q.
    Computes real r and p-value from the data.
    """
    # Ensure data is clean
    clean_data = data[[x_col, y_col]].dropna()
    if len(clean_data) < 3:
        logger.log("generate_scatter_plot", error="Insufficient data points for correlation")
        return None

    x = clean_data[x_col].values
    y = clean_data[y_col].values

    # Calculate real correlation and p-value
    r, p_val = stats.pearsonr(x, y)

    # Determine significance based on FDR corrected q (if available in kwargs) or p
    q = kwargs.get('q', p_val)
    significant = q < 0.05

    plt.figure(figsize=(10, 6))
    
    # Scatter
    plt.scatter(x, y, alpha=0.6, edgecolors='w', s=50)
    
    # Regression line
    z = np.polyfit(x, y, 1)
    p = np.poly1d(z)
    plt.plot(x, p(x), "r--", label=f'y = {z[0]:.2f}x + {z[1]:.2f}')
    
    # Annotate with real r and p/q
    annotation_text = f"r = {r:.2f}\np = {p_val:.3f}\nq = {q:.3f}"
    if significant:
        annotation_text += " (sig)"
    
    plt.text(0.05, 0.95, annotation_text, 
             transform=plt.gca().transAxes, 
             verticalalignment='top',
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend()
    
    # Ensure directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    logger.log("generate_scatter_plot", path=output_path, r=r, p=p_val, q=q, significant=significant)
    return output_path

def main():
    """Main runner for scatter plots.
    
    Loads correlation results to determine which metrics to plot and their q-values.
    Loads full metrics data to perform the actual plotting.
    """
    # Load correlation results to get q-values and metric names
    corr_path = "data/analysis/correlations.csv"
    if not os.path.exists(corr_path):
        logger.log("scatter_main", error="Correlation results not found", path=corr_path)
        print(f"Error: {corr_path} not found. Run correlations analysis first.")
        return

    corr_df = pd.read_csv(corr_path)
    
    # Load full metrics data
    full_path = "data/analysis/full_metrics.csv"
    if not os.path.exists(full_path):
        logger.log("scatter_main", error="Full metrics data not found", path=full_path)
        print(f"Error: {full_path} not found.")
        return
    
    full_df = pd.read_csv(full_path)

    if "motor_score" not in full_df.columns:
        logger.log("scatter_main", error="motor_score column not found in full_metrics.csv")
        return

    # Iterate through significant correlations or all metrics in correlation results
    metrics_to_plot = corr_df['metric'].tolist()
    
    for _, row in corr_df.iterrows():
        metric = row["metric"]
        q = row.get("q", 1.0) # Default to 1 if not found
        
        if metric not in full_df.columns:
            logger.log("scatter_main", warning=f"Metric {metric} not found in full_metrics.csv, skipping")
            continue

        out_path = f"figures/scatter_{metric}.png"
        generate_scatter_plot(
            full_df, 
            metric, 
            "motor_score", 
            out_path, 
            title=f"{metric} vs Motor Score",
            xlabel=metric,
            ylabel="Motor Score",
            q=q
        )
        print(f"Generated plot: {out_path}")

if __name__ == "__main__":
    main()
