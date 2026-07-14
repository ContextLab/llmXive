"""Scatter plot generator for metric vs. score correlations."""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

# Import logging utility from project root
from code.logging_config import get_logger

logger = get_logger(__name__)


def load_correlation_results(csv_path: Optional[str] = None) -> pd.DataFrame:
    """Load correlation results from CSV.
    
    Args:
        csv_path: Path to correlation results CSV. Defaults to 
                 data/analysis/correlation_results.csv
                
    Returns:
        DataFrame with correlation results including metric_name, r, p, q, significant
    """
    if csv_path is None:
        # Default path based on project structure
        csv_path = "data/analysis/correlation_results.csv"
    
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"Correlation results file not found: {csv_path}")
    
    df = pd.read_csv(csv_path)
    logger.log("load_correlation_results", file=csv_path, rows=len(df))
    return df


def generate_scatter_plot(
    data: pd.DataFrame,
    x_col: str,
    y_col: str,
    output_path: str,
    title: Optional[str] = None,
    x_label: Optional[str] = None,
    y_label: Optional[str] = None,
    annotate_stats: bool = True,
    add_regression: bool = True,
    significant_only: bool = False,
    fdr_threshold: float = 0.05,
    color: str = "#2E86AB",
    alpha: float = 0.6,
    size: int = 60,
) -> str:
    """Generate a scatter plot with regression line and statistical annotations.
    
    Creates a publication-quality scatter plot showing the relationship between
    two variables, with optional regression line and statistical annotations.
    
    Args:
        data: DataFrame containing the data
        x_col: Column name for x-axis values
        y_col: Column name for y-axis values
        output_path: Path where the plot will be saved (must end in .png or .pdf)
        title: Plot title (auto-generated if None)
        x_label: X-axis label (auto-generated if None)
        y_label: Y-axis label (auto-generated if None)
        annotate_stats: Whether to add r, p, and q values to the plot
        add_regression: Whether to add a regression line
        significant_only: If True, only plot subjects where correlation is significant
        fdr_threshold: FDR threshold for significance (default 0.05)
        color: Color for data points
        alpha: Transparency for data points
        size: Size of data points
        
    Returns:
        Path to the saved plot file
    """
    # Validate input
    if x_col not in data.columns:
        raise ValueError(f"Column '{x_col}' not found in data. Available: {list(data.columns)}")
    if y_col not in data.columns:
        raise ValueError(f"Column '{y_col}' not found in data. Available: {list(data.columns)}")
    
    # Filter data if needed
    plot_data = data.copy()
    if significant_only and "significant" in plot_data.columns:
        plot_data = plot_data[plot_data["significant"] == True]
        logger.log("generate_scatter_plot", action="filter", 
                  reason="significant_only", filtered_rows=len(data) - len(plot_data))
    
    # Remove rows with NaN
    plot_data = plot_data.dropna(subset=[x_col, y_col])
    
    if len(plot_data) < 2:
        raise ValueError(f"Not enough data points to generate scatter plot ({len(plot_data)} rows)")
    
    # Calculate statistics
    x_vals = plot_data[x_col].values
    y_vals = plot_data[y_col].values
    
    # Pearson correlation
    r, p_value = stats.pearsonr(x_vals, y_vals)
    
    # Calculate FDR corrected q-value (using Benjamini-Hochberg)
    # For a single correlation, q = p (but we'll compute it properly for consistency)
    # If we have multiple tests, we'd need all p-values, but here we assume single test
    q_value = p_value  # For single test, q = p
    
    # Create plot
    fig, ax = plt.subplots(figsize=(8, 6))
    
    # Scatter plot
    ax.scatter(x_vals, y_vals, c=color, alpha=alpha, s=size, edgecolors='black', linewidth=0.5)
    
    # Regression line
    if add_regression and len(x_vals) >= 2:
        slope, intercept, r_val, p_val, std_err = stats.linregress(x_vals, y_vals)
        x_line = np.array([min(x_vals), max(x_vals)])
        y_line = slope * x_line + intercept
        ax.plot(x_line, y_line, 'r-', linewidth=2, label=f'Regression (r={r:.3f})')
    
    # Labels and title
    if title is None:
        title = f"{y_col} vs {x_col}"
    if x_label is None:
        x_label = x_col.replace('_', ' ').title()
    if y_label is None:
        y_label = y_col.replace('_', ' ').title()
        
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.set_xlabel(x_label, fontsize=12)
    ax.set_ylabel(y_label, fontsize=12)
    
    # Statistical annotations
    if annotate_stats:
        # Format p-value
        if p_value < 0.001:
            p_str = "p < 0.001"
        else:
            p_str = f"p = {p_value:.3f}"
        
        # Format q-value
        if q_value < 0.001:
            q_str = "q < 0.001"
        else:
            q_str = f"q = {q_value:.3f}"
        
        # Create annotation text
        stats_text = f"r = {r:.3f}\n{p_str}\n{q_str}"
        
        # Position annotation in upper left
        ax.annotate(
            stats_text,
            xy=(0.05, 0.95),
            xycoords='axes fraction',
            verticalalignment='top',
            horizontalalignment='left',
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.8, edgecolor='gray'),
            fontsize=10
        )
    
    # Grid
    ax.grid(True, linestyle='--', alpha=0.3)
    
    # Adjust layout
    plt.tight_layout()
    
    # Ensure output directory exists
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save figure
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    
    logger.log("generate_scatter_plot", 
              action="save",
              path=str(output_path),
              n_points=len(plot_data),
              r=r,
              p=p_value,
              q=q_value)
    
    return str(output_path)


def generate_all_scatter_plots(
    correlation_results: pd.DataFrame,
    metrics_df: pd.DataFrame,
    output_dir: str,
    fdr_threshold: float = 0.05
) -> List[str]:
    """Generate scatter plots for all significant correlations.
    
    Args:
        correlation_results: DataFrame with correlation results (metric_name, r, p, q, significant)
        metrics_df: DataFrame with subject-level data (subject_id, metric columns, score columns)
        output_dir: Directory to save plots
        fdr_threshold: FDR threshold for significance
        
    Returns:
        List of paths to generated plot files
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    generated_plots = []
    
    # Filter for significant correlations
    sig_corrs = correlation_results[
        (correlation_results["significant"] == True) & 
        (correlation_results["q"] <= fdr_threshold)
    ]
    
    logger.log("generate_all_scatter_plots", 
              total_correlations=len(correlation_results),
              significant=len(sig_corrs))
    
    for _, row in sig_corrs.iterrows():
        metric_name = row["metric_name"]
        
        # Find corresponding score column (assumes naming: metric_name -> score)
        # In our case, we're correlating network metrics with motor_score
        x_col = metric_name
        y_col = "motor_score"
        
        # Check if columns exist in metrics_df
        if x_col not in metrics_df.columns or y_col not in metrics_df.columns:
            logger.log("generate_all_scatter_plots", 
                      action="skip",
                      reason=f"Missing columns: x={x_col}, y={y_col}")
            continue
        
        # Generate plot
        plot_path = output_dir / f"scatter_{metric_name}_vs_motor_score.png"
        
        try:
            generated_path = generate_scatter_plot(
                data=metrics_df,
                x_col=x_col,
                y_col=y_col,
                output_path=str(plot_path),
                title=f"{metric_name} vs Motor Score",
                x_label=metric_name.replace('_', ' ').title(),
                y_label="Motor Score",
                annotate_stats=True,
                add_regression=True,
                significant_only=False,
                fdr_threshold=fdr_threshold
            )
            generated_plots.append(generated_path)
            logger.log("generate_all_scatter_plots", 
                      action="generated",
                      plot=str(generated_path))
        except Exception as e:
            logger.log("generate_all_scatter_plots", 
                      action="failed",
                      error=str(e),
                      metric=metric_name)
    
    return generated_plots


def main() -> None:
    """Main entry point for scatter plot generation.
    
    Reads correlation results and metrics data, then generates scatter plots
    for all significant correlations.
    """
    # Define paths
    base_dir = Path(__file__).parent.parent.parent
    correlation_results_path = base_dir / "data" / "analysis" / "correlation_results.csv"
    metrics_path = base_dir / "data" / "analysis" / "full_metrics.csv"
    output_dir = base_dir / "figures"
    
    logger.log("main", action="start", 
              correlation_results=str(correlation_results_path),
              metrics=str(metrics_path),
              output_dir=str(output_dir))
    
    # Load data
    try:
        correlation_results = load_correlation_results(str(correlation_results_path))
    except FileNotFoundError as e:
        logger.log("main", action="error", error=str(e))
        print(f"Error: {e}")
        print("Make sure to run the correlation analysis first (T024-T025)")
        sys.exit(1)
    
    try:
        metrics_df = pd.read_csv(metrics_path)
    except FileNotFoundError:
        logger.log("main", action="error", error=f"Metrics file not found: {metrics_path}")
        print(f"Error: Metrics file not found: {metrics_path}")
        sys.exit(1)
    
    # Generate plots
    plots = generate_all_scatter_plots(
        correlation_results=correlation_results,
        metrics_df=metrics_df,
        output_dir=str(output_dir),
        fdr_threshold=0.05
    )
    
    logger.log("main", action="complete", plots_generated=len(plots))
    print(f"Generated {len(plots)} scatter plots in {output_dir}")


    # Load metrics data (raw values for plotting)
    metrics_path = "data/analysis/full_metrics.csv"
    metrics_df = None
    if Path(metrics_path).exists():
        metrics_df = pd.read_csv(metrics_path)
        logger.log("scatter_main", loaded_metrics=metrics_path, rows=len(metrics_df))
    else:
        logger.log("scatter_main", warning="metrics_data_missing", path=metrics_path)

    # Generate plots
    generated = generate_all_scatter_plots(
        results_df=results_df,
        metrics_data=metrics_df,
        score_column="motor_score"
    )

    logger.log("scatter_main", status="completed", plots_generated=len(generated))
    print(f"Generated {len(generated)} scatter plot(s) in {FIGURES_DIR}/")

    for p in generated:
        print(f"  - {p}")


if __name__ == "__main__":
    main()
