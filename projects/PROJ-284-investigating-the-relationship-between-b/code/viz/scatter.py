"""
Visualization module for generating scatter plots of metric vs. score correlations.
Implements T031 and supports T029 tests.
"""
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from scipy import stats
import logging

# Ensure project root is in path for imports
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.logging_config import get_logger

logger = get_logger(__name__)

def generate_scatter_plot(
    data: pd.DataFrame,
    x_col: str,
    y_col: str,
    output_path: str,
    title: str = "Correlation Plot",
    xlabel: str = "Metric",
    ylabel: str = "Score",
    r: Optional[float] = None,
    p: Optional[float] = None,
    q: Optional[float] = None,
    min_points: int = 3
) -> Optional[str]:
    """
    Generate a scatter plot with regression line and correlation annotations.
    
    Args:
        data: DataFrame containing the data.
        x_col: Column name for x-axis.
        y_col: Column name for y-axis.
        output_path: Path to save the output PNG file.
        title: Plot title.
        xlabel: X-axis label.
        ylabel: Y-axis label.
        r: Pre-computed correlation coefficient (optional).
        p: Pre-computed p-value (optional).
        q: Pre-computed FDR-corrected p-value (optional).
        min_points: Minimum number of data points required.
        
    Returns:
        Path to the saved file if successful, None otherwise.
    """
    # Validate data
    if data is None or x_col not in data.columns or y_col not in data.columns:
        logger.log("scatter_plot_error", message="Invalid data or columns provided")
        return None
    
    valid_data = data[[x_col, y_col]].dropna()
    
    if len(valid_data) < min_points:
        logger.log("scatter_plot_error", message=f"Insufficient data points: {len(valid_data)} < {min_points}")
        return None
    
    x = valid_data[x_col].values
    y = valid_data[y_col].values
    
    # Calculate correlation if not provided
    if r is None or p is None:
        try:
            r, p = stats.pearsonr(x, y)
            logger.log("correlation_calculated", r=r, p=p)
        except Exception as e:
            logger.log("correlation_error", message=str(e))
            return None
    
    # Create plot
    plt.figure(figsize=(10, 8))
    plt.scatter(x, y, alpha=0.6, edgecolors='k', s=50)
    
    # Add regression line
    m, b = np.polyfit(x, y, 1)
    x_line = np.linspace(x.min(), x.max(), 100)
    plt.plot(x_line, m * x_line + b, 'r-', linewidth=2, label=f'Regression (r={r:.3f})')
    
    # Annotations
    annotation_text = f"r = {r:.3f}\np = {p:.4f}"
    if q is not None:
        annotation_text += f"\nq (FDR) = {q:.4f}"
    
    plt.text(
        0.05, 0.95, annotation_text,
        transform=plt.gca().transAxes,
        fontsize=12,
        verticalalignment='top',
        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5)
    )
    
    plt.title(title, fontsize=14, fontweight='bold')
    plt.xlabel(xlabel, fontsize=12)
    plt.ylabel(ylabel, fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend()
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    # Save plot
    try:
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        logger.log("scatter_plot_saved", path=output_path, size=os.path.getsize(output_path))
        return output_path
    except Exception as e:
        logger.log("scatter_save_error", message=str(e))
        plt.close()
        return None

def main():
    """
    Main entry point for standalone execution.
    Loads real correlation results from data/analysis/correlations.csv
    and generates scatter plots for each significant metric.
    """
    # Define paths
    project_root = Path(__file__).parent.parent.parent
    corr_file = project_root / "data" / "analysis" / "correlations.csv"
    output_dir = project_root / "data" / "analysis" / "figures"
    
    if not corr_file.exists():
        logger.log("file_not_found", path=str(corr_file), message="Correlation results file not found. Run analysis first.")
        print(f"Error: {corr_file} not found.")
        return 1
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load real data
    try:
        df = pd.read_csv(corr_file)
        logger.log("data_loaded", path=str(corr_file), rows=len(df))
    except Exception as e:
        logger.log("data_load_error", message=str(e))
        print(f"Failed to load {corr_file}: {e}")
        return 1
    
    # Required columns for plotting
    required_cols = ['metric_name', 'subject_id', 'value', 'motor_score', 'r', 'p', 'q']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        logger.log("missing_columns", columns=missing)
        print(f"Missing required columns in {corr_file}: {missing}")
        return 1
    
    # Filter for significant correlations (q < 0.05)
    significant = df[df['q'] < 0.05]
    logger.log("filtering_significant", total=len(df), significant=len(significant))
    
    if significant.empty:
        logger.log("no_significant_results", message="No significant correlations found to plot.")
        print("No significant correlations found. No plots generated.")
        return 0
    
    # Group by metric to plot metric vs motor_score
    # We assume the 'value' column holds the metric value and 'motor_score' holds the behavioral score
    plots_generated = 0
    
    for metric_name in significant['metric_name'].unique():
        subset = significant[significant['metric_name'] == metric_name]
        
        # Use mean value per subject if multiple rows exist (though schema suggests one per subject)
        plot_data = subset.groupby('subject_id').agg({
            'value': 'mean',
            'motor_score': 'mean',
            'r': 'first',
            'p': 'first',
            'q': 'first'
        }).reset_index()
        
        # Generate plot
        output_path = output_dir / f"scatter_{metric_name.replace(' ', '_').replace('-', '_')}.png"
        
        result_path = generate_scatter_plot(
            data=plot_data,
            x_col='value',
            y_col='motor_score',
            output_path=str(output_path),
            title=f"{metric_name} vs Motor Score",
            xlabel=metric_name,
            ylabel="Motor Score",
            r=plot_data['r'].iloc[0],
            p=plot_data['p'].iloc[0],
            q=plot_data['q'].iloc[0]
        )
        
        if result_path:
            plots_generated += 1
            print(f"Generated: {result_path}")
    
    logger.log("plots_complete", count=plots_generated)
    print(f"Total plots generated: {plots_generated}")
    return 0

if __name__ == "__main__":
    main()