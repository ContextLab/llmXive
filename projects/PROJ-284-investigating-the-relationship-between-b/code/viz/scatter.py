"""
Scatter plot generator for metric vs. score correlations.
Generates publication-quality plots with regression lines and annotated statistics.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

# Import from project modules
from code.logging_config import get_logger
from code.analysis.correlations import apply_fdr_correction, run_correlations_with_fd_covariate

logger = get_logger(__name__)

# Constants
FIGURE_DIR = Path("data/figures")
FIGURE_DIR.mkdir(parents=True, exist_ok=True)

# Colors and styles
COLOR_PRIMARY = "#2E86AB"
COLOR_SECONDARY = "#A23B72"
COLOR_REGRESSION = "#F18F01"
FONT_SIZE_LABEL = 12
FONT_SIZE_TITLE = 14
LINE_WIDTH = 1.5


def load_correlation_results() -> pd.DataFrame:
    """
    Load correlation results from the analysis output.
    Returns a DataFrame with columns: metric_name, r, p, q, significant, subject_id, metric_value, score_value
    """
    # Expected path based on task dependencies
    corr_path = Path("data/analysis/correlations.csv")
    
    if not corr_path.exists():
        logger.log("file_missing", path=str(corr_path))
        raise FileNotFoundError(f"Correlation results not found at {corr_path}. "
                              "Run analysis pipeline first.")
    
    df = pd.read_csv(corr_path)
    
    # Ensure required columns exist
    required_cols = ['metric_name', 'r', 'p', 'q', 'significant', 'subject_id', 'metric_value', 'score_value']
    missing_cols = [c for c in required_cols if c not in df.columns]
    
    if missing_cols:
        logger.log("missing_columns", missing=missing_cols)
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    logger.log("loaded_correlations", rows=len(df))
    return df


def generate_scatter_plot(
    metric_name: str,
    df: pd.DataFrame,
    output_path: Optional[Union[str, Path]] = None,
    dpi: int = 300,
    figsize: Tuple[int, int] = (8, 6)
) -> Path:
    """
    Generate a scatter plot for a specific metric vs. score.
    
    Args:
        metric_name: Name of the metric to plot (e.g., 'modularity', 'global_efficiency')
        df: DataFrame containing correlation data
        output_path: Optional path to save the figure. If None, uses default naming.
        dpi: Resolution for saved figure
        figsize: Figure dimensions (width, height)
    
    Returns:
        Path to the saved figure file
    """
    # Filter data for this metric
    metric_data = df[df['metric_name'] == metric_name].copy()
    
    if len(metric_data) == 0:
        logger.log("no_data_for_metric", metric=metric_name)
        raise ValueError(f"No data found for metric: {metric_name}")
    
    # Extract values
    x = metric_data['metric_value'].values
    y = metric_data['score_value'].values
    r_val = metric_data['r'].iloc[0]
    p_val = metric_data['p'].iloc[0]
    q_val = metric_data['q'].iloc[0]
    is_sig = metric_data['significant'].iloc[0]
    
    # Calculate regression line
    slope, intercept, r_calc, p_calc, std_err = stats.linregress(x, y)
    x_line = np.linspace(x.min(), x.max(), 100)
    y_line = slope * x_line + intercept
    
    # Create figure
    fig, ax = plt.subplots(figsize=figsize)
    
    # Scatter plot
    ax.scatter(x, y, color=COLOR_PRIMARY, alpha=0.7, s=50, edgecolors='white', linewidth=0.5)
    
    # Regression line
    ax.plot(x_line, y_line, color=COLOR_REGRESSION, linewidth=LINE_WIDTH, linestyle='--')
    
    # Add confidence interval (optional, 95% CI)
    y_upper = y_line + 1.96 * std_err
    y_lower = y_line - 1.96 * std_err
    ax.fill_between(x_line, y_lower, y_upper, color=COLOR_REGRESSION, alpha=0.2)
    
    # Labels and title
    ax.set_xlabel(metric_name.replace('_', ' ').title(), fontsize=FONT_SIZE_LABEL)
    ax.set_ylabel('Sensorimotor Performance Score', fontsize=FONT_SIZE_LABEL)
    ax.set_title(f'{metric_name.replace("_", " ").title()} vs. Sensorimotor Performance', 
                fontsize=FONT_SIZE_TITLE)
    
    # Annotate statistics
    sig_text = "***" if is_sig else ""
    stat_text = (
        f"r = {r_val:.3f} {sig_text}\n"
        f"p = {p_val:.3f}\n"
        f"q (FDR) = {q_val:.3f}"
    )
    
    # Position annotation in top-left corner
    ax.text(
        0.05, 0.95, stat_text,
        transform=ax.transAxes,
        fontsize=FONT_SIZE_LABEL,
        verticalalignment='top',
        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5)
    )
    
    # Grid
    ax.grid(True, linestyle=':', alpha=0.6)
    
    # Adjust layout
    plt.tight_layout()
    
    # Determine output path
    if output_path is None:
        safe_name = metric_name.replace(' ', '_').replace('/', '_')
        output_path = FIGURE_DIR / f"scatter_{safe_name}.png"
    else:
        output_path = Path(output_path)
    
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save figure
    fig.savefig(output_path, dpi=dpi, bbox_inches='tight')
    plt.close(fig)
    
    logger.log("scatter_plot_generated", metric=metric_name, path=str(output_path))
    return output_path


def generate_all_scatter_plots(
    df: Optional[pd.DataFrame] = None,
    metrics: Optional[List[str]] = None
) -> List[Path]:
    """
    Generate scatter plots for all metrics in the correlation results.
    
    Args:
        df: Optional DataFrame. If None, loads from default path.
        metrics: Optional list of specific metrics to plot. If None, plots all.
    
    Returns:
        List of paths to generated figure files
    """
    if df is None:
        df = load_correlation_results()
    
    if metrics is None:
        metrics = df['metric_name'].unique().tolist()
    
    output_paths = []
    
    for metric in metrics:
        try:
            path = generate_scatter_plot(metric, df)
            output_paths.append(path)
            logger.log("plot_success", metric=metric)
        except Exception as e:
            logger.log("plot_failed", metric=metric, error=str(e))
            # Continue with other metrics rather than failing entirely
    
    logger.log("all_plots_generated", count=len(output_paths))
    return output_paths


def main() -> None:
    """
    Main entry point for scatter plot generation.
    Loads correlation results and generates plots for all metrics.
    """
    logger.log("scatter_plot_main_start")
    
    try:
        # Load data
        df = load_correlation_results()
        
        # Generate all plots
        output_files = generate_all_scatter_plots(df)
        
        print(f"Generated {len(output_files)} scatter plots:")
        for path in output_files:
            print(f"  - {path}")
            
    except FileNotFoundError as e:
        logger.log("main_failed", error=str(e))
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.log("main_failed", error=str(e))
        print(f"Unexpected error: {e}")
        sys.exit(1)
    
    logger.log("scatter_plot_main_complete")


if __name__ == "__main__":
    main()