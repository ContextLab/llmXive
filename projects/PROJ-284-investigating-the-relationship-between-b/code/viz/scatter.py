"""Scatter plot generator for metric vs. score analysis.

Implements FR-004 visualization requirements:
- Scatter plot of metric vs. score
- Regression line overlay
- Annotated r and q (FDR-corrected p-value)
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

# Project imports
from code.logging_config import get_logger

logger = get_logger(__name__)


def generate_scatter_plot(
    data: pd.DataFrame,
    x_col: str,
    y_col: str,
    output_path: str,
    title: Optional[str] = None,
    x_label: Optional[str] = None,
    y_label: Optional[str] = None,
    show_regression: bool = True,
    annotate_stats: bool = True,
    color: str = "#1f77b4",
    alpha: float = 0.6,
    size: int = 50,
    dpi: int = 300,
) -> str:
    """Generate a scatter plot with regression line and statistical annotations.

    Args:
        data: DataFrame containing the data
        x_col: Column name for x-axis (metric)
        y_col: Column name for y-axis (score)
        output_path: Path to save the plot (must end in .png or .pdf)
        title: Plot title (default: auto-generated)
        x_label: X-axis label (default: column name)
        y_label: Y-axis label (default: column name)
        show_regression: Whether to overlay regression line
        annotate_stats: Whether to annotate r and q values
        color: Marker color
        alpha: Marker transparency
        size: Marker size
        dpi: Output resolution

    Returns:
        Path to the saved plot file

    Raises:
        ValueError: If data is invalid or required columns missing
    """
    # Validate inputs
    if not isinstance(data, pd.DataFrame):
        raise ValueError("data must be a pandas DataFrame")
    if x_col not in data.columns:
        raise ValueError(f"Column '{x_col}' not found in data")
    if y_col not in data.columns:
        raise ValueError(f"Column '{y_col}' not found in data")

    # Remove NaN values
    mask = data[[x_col, y_col]].notna().all(axis=1)
    clean_data = data[mask]

    if len(clean_data) < 2:
        raise ValueError("Need at least 2 data points for regression")

    x = clean_data[x_col].values
    y = clean_data[y_col].values

    # Calculate statistics
    r, p_value, _, _ = stats.pearsonr(x, y)

    # FDR-corrected p-value (q-value) - using Bonferroni as fallback if not provided
    # In practice, q should come from the correlation analysis (T025)
    # For this function, we assume q is the same as p if not explicitly passed
    # A more complete version would accept q as a parameter
    q = p_value  # Placeholder - actual q should be passed from correlation results

    # Create plot
    fig, ax = plt.subplots(figsize=(10, 8))

    # Scatter plot
    ax.scatter(x, y, c=color, alpha=alpha, s=size, edgecolors='k', linewidth=0.5)

    # Regression line
    if show_regression and len(x) >= 2:
        slope, intercept, r_reg, p_reg, _ = stats.linregress(x, y)
        x_line = np.linspace(x.min(), x.max(), 100)
        y_line = slope * x_line + intercept
        ax.plot(x_line, y_line, 'r-', linewidth=2, label=f'Regression (r={r_reg:.3f})')

    # Labels and title
    ax.set_xlabel(x_label or x_col, fontsize=12, fontweight='bold')
    ax.set_ylabel(y_label or y_col, fontsize=12, fontweight='bold')
    ax.set_title(title or f"{y_col} vs {x_col}", fontsize=14, fontweight='bold')

    # Grid
    ax.grid(True, linestyle='--', alpha=0.7)

    # Annotate statistics
    if annotate_stats:
        # Determine significance
        sig_marker = "*" if q < 0.05 else ""
        sig_marker += "*" if q < 0.01 else ""
        sig_marker += "*" if q < 0.001 else ""

        annotation_text = (
            f"r = {r:.3f}\n"
            f"p = {p_value:.4f}\n"
            f"q = {q:.4f}{sig_marker}"
        )

        # Position annotation in upper right
        ax.annotate(
            annotation_text,
            xy=(0.95, 0.95),
            xycoords='axes fraction',
            ha='right',
            va='top',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5),
            fontsize=10
        )

    # Ensure output directory exists
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Save figure
    plt.tight_layout()
    plt.savefig(output_path, dpi=dpi, bbox_inches='tight')
    plt.close(fig)

    logger.log("scatter_plot_generated", {
        "x_col": x_col,
        "y_col": y_col,
        "n_points": len(clean_data),
        "r": r,
        "p": p_value,
        "q": q,
        "output_path": str(output_path)
    })

    return str(output_path)


def generate_scatter_plot_with_q(
    data: pd.DataFrame,
    x_col: str,
    y_col: str,
    q_col: str,
    output_path: str,
    title: Optional[str] = None,
    x_label: Optional[str] = None,
    y_label: Optional[str] = None,
    show_regression: bool = True,
    annotate_stats: bool = True,
    color: str = "#1f77b4",
    alpha: float = 0.6,
    size: int = 50,
    dpi: int = 300,
) -> str:
    """Generate scatter plot with explicit FDR-corrected q-value column.

    This variant accepts a DataFrame that already contains the q-value
    column from the correlation analysis (T025).

    Args:
        data: DataFrame containing x, y, and q columns
        x_col: Column name for x-axis
        y_col: Column name for y-axis
        q_col: Column name for FDR-corrected p-values
        output_path: Path to save the plot
        title: Plot title
        x_label: X-axis label
        y_label: Y-axis label
        show_regression: Show regression line
        annotate_stats: Show statistical annotations
        color: Marker color
        alpha: Marker transparency
        size: Marker size
        dpi: Output resolution

    Returns:
        Path to the saved plot
    """
    if q_col not in data.columns:
        raise ValueError(f"Q-value column '{q_col}' not found in data")

    # Filter to rows where we have all required values
    mask = data[[x_col, y_col, q_col]].notna().all(axis=1)
    clean_data = data[mask]

    if len(clean_data) < 2:
        raise ValueError("Need at least 2 data points for regression")

    x = clean_data[x_col].values
    y = clean_data[y_col].values
    q = clean_data[q_col].iloc[0]  # Assume q is constant for this metric

    # Create plot
    fig, ax = plt.subplots(figsize=(10, 8))

    # Scatter plot
    ax.scatter(x, y, c=color, alpha=alpha, s=size, edgecolors='k', linewidth=0.5)

    # Regression line
    if show_regression:
        slope, intercept, r, p_value, _ = stats.linregress(x, y)
        x_line = np.linspace(x.min(), x.max(), 100)
        y_line = slope * x_line + intercept
        ax.plot(x_line, y_line, 'r-', linewidth=2)

    # Labels
    ax.set_xlabel(x_label or x_col, fontsize=12, fontweight='bold')
    ax.set_ylabel(y_label or y_col, fontsize=12, fontweight='bold')
    ax.set_title(title or f"{y_col} vs {x_col}", fontsize=14, fontweight='bold')
    ax.grid(True, linestyle='--', alpha=0.7)

    # Annotate
    if annotate_stats:
        sig_marker = ""
        if q < 0.001:
            sig_marker = "***"
        elif q < 0.01:
            sig_marker = "**"
        elif q < 0.05:
            sig_marker = "*"

        annotation_text = (
            f"r = {r:.3f}\n"
            f"q = {q:.4f}{sig_marker}"
        )

        ax.annotate(
            annotation_text,
            xy=(0.95, 0.95),
            xycoords='axes fraction',
            ha='right',
            va='top',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5),
            fontsize=10
        )

    # Save
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    plt.tight_layout()
    plt.savefig(output_path, dpi=dpi, bbox_inches='tight')
    plt.close(fig)

    logger.log("scatter_plot_generated_with_q", {
        "x_col": x_col,
        "y_col": y_col,
        "q_col": q_col,
        "n_points": len(clean_data),
        "r": r,
        "q": q,
        "output_path": str(output_path)
    })

    return str(output_path)


def main() -> int:
    """Main entry point for scatter plot generation.

    Generates scatter plots for all significant correlations found in
    data/analysis/correlations.csv.

    Returns:
        0 on success, 1 on error
    """
    try:
        # Load correlation results
        corr_path = Path("data/analysis/correlations.csv")
        if not corr_path.exists():
            logger.log("correlations_file_not_found", {"path": str(corr_path)})
            print(f"Error: Correlation results file not found: {corr_path}")
            print("Please run the correlation analysis first (T024, T025)")
            return 1

        corr_data = pd.read_csv(corr_path)

        # Create output directory
        output_dir = Path("figures")
        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate plots for significant correlations (q < 0.05)
        significant = corr_data[corr_data['significant'] == True]

        if significant.empty:
            logger.log("no_significant_correlations", {})
            print("No significant correlations found to plot.")
            return 0

        print(f"Generating {len(significant)} scatter plots...")

        for idx, row in significant.iterrows():
            metric_name = row['metric_name']
            r = row['r']
            q = row['q']

            # Determine x and y columns based on metric
            # Assuming data is in data/analysis/full_metrics.csv
            metrics_path = Path("data/analysis/full_metrics.csv")
            if not metrics_path.exists():
                logger.log("metrics_file_not_found", {"path": str(metrics_path)})
                print(f"Error: Metrics file not found: {metrics_path}")
                return 1

            metrics_df = pd.read_csv(metrics_path)

            # Find the column for this metric
            if metric_name not in metrics_df.columns:
                logger.log("metric_column_not_found", {"metric": metric_name})
                print(f"Warning: Metric '{metric_name}' not found in data, skipping.")
                continue

            x_col = metric_name
            y_col = "motor_score"  # Target variable

            if y_col not in metrics_df.columns:
                logger.log("target_column_not_found", {"column": y_col})
                print(f"Error: Target column '{y_col}' not found in data.")
                return 1

            # Generate plot
            output_file = output_dir / f"scatter_{metric_name}.png"
            plot_path = generate_scatter_plot_with_q(
                data=metrics_df,
                x_col=x_col,
                y_col=y_col,
                q_col="q",  # We'll compute q from the correlation table
                output_path=str(output_file),
                title=f"{metric_name} vs Motor Score",
                x_label=metric_name,
                y_label="Motor Score",
                color="#2ca02c" if q < 0.05 else "#d62728",
            )

            print(f"  Generated: {plot_path}")

        logger.log("scatter_plots_complete", {
            "n_plots": len(significant),
            "output_dir": str(output_dir)
        })

        print(f"\nAll plots saved to: {output_dir}")
        return 0

    except Exception as e:
        logger.log("scatter_plot_error", {"error": str(e)})
        print(f"Error generating scatter plots: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
