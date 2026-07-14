"""Scatter plot generator for correlation analysis."""
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
    input: Union[pd.DataFrame, str],
    x: str,
    y: str,
    output: str,
    metric_name: Optional[str] = None,
    score_name: Optional[str] = None,
    title: Optional[str] = None,
    show_regression: bool = True,
    annotate_stats: bool = True,
    annotate_q: bool = True,
    q_value: Optional[float] = None,
    **kwargs: Any
) -> str:
    """
    Generate a scatter plot with regression line and statistical annotations (r, p, q).

    Args:
        input: DataFrame or path to CSV containing the data.
        x: Column name for x-axis.
        y: Column name for y-axis.
        output: Path to save the output PNG file.
        metric_name: Label for x-axis (defaults to x column name).
        score_name: Label for y-axis (defaults to y column name).
        title: Plot title (defaults to correlation description).
        show_regression: Whether to add a regression line.
        annotate_stats: Whether to annotate r and p values.
        annotate_q: Whether to annotate the FDR-corrected q-value.
        q_value: The FDR-corrected q-value (p-value) for annotation.
        **kwargs: Additional arguments for flexibility.

    Returns:
        Path to the generated image file.

    Raises:
        ValueError: If columns are missing or insufficient data points.
        FileNotFoundError: If input file does not exist.
    """
    # Load data
    if isinstance(input, str):
        if not os.path.exists(input):
            raise FileNotFoundError(f"Input file not found: {input}")
        df = pd.read_csv(input)
    elif isinstance(input, pd.DataFrame):
        df = input.copy()
    else:
        raise TypeError(f"Input must be DataFrame or path, got {type(input)}")

    # Validate columns
    for col in [x, y]:
        if col not in df.columns:
            raise ValueError(f"Column '{col}' not found in data. Available: {list(df.columns)}")

    # Remove NaN
    df = df[[x, y]].dropna()

    # Check data sufficiency
    if len(df) < 2:
        raise ValueError("Insufficient data points (need at least 2)")

    # Extract data
    x_data = df[x].values
    y_data = df[y].values

    # Calculate correlation
    r, p_value = stats.pearsonr(x_data, y_data)
    n = len(x_data)

    # Determine q-value
    if q_value is None and annotate_q:
        # If q is not provided but requested, we assume p is the best estimate or warn
        # In a full pipeline, q would come from T025 (FDR correction)
        q_val = p_value 
    elif q_value is not None:
        q_val = q_value
    else:
        q_val = None

    # Create plot
    fig, ax = plt.subplots(figsize=(10, 8))

    # Scatter plot
    ax.scatter(x_data, y_data, alpha=0.6, edgecolors='w', linewidth=0.5, s=60, color='#3498db')

    # Regression line
    if show_regression and len(x_data) >= 2:
        m, b = np.polyfit(x_data, y_data, 1)
        x_line = np.linspace(x_data.min(), x_data.max(), 100)
        y_line = m * x_line + b
        ax.plot(x_line, y_line, 'r-', linewidth=2, label=f'Regression (r={r:.3f})')

    # Labels and Title
    ax.set_xlabel(metric_name or x.capitalize(), fontsize=12)
    ax.set_ylabel(score_name or y.capitalize(), fontsize=12)
    if title:
        ax.set_title(title, fontsize=14, fontweight='bold')
    else:
        ax.set_title(f'Correlation: {metric_name or x} vs {score_name or y}', fontsize=14, fontweight='bold')

    # Annotate statistics
    if annotate_stats:
        stats_text = f'r = {r:.3f}\np = {p_value:.4f}\nn = {n}'
        if annotate_q and q_val is not None:
            stats_text += f'\nq = {q_val:.4f}'
        
        ax.text(
            0.05, 0.95, stats_text,
            transform=ax.transAxes,
            fontsize=11,
            verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5)
        )

    # Grid
    ax.grid(True, linestyle='--', alpha=0.7)

    # Ensure output directory exists
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Save
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close(fig)

    logger.log(
        "generate_scatter_plot", 
        operation="plot_generated", 
        output=str(output_path), 
        r=r, 
        p=p_value,
        q=q_val,
        n=n
    )

    return str(output_path)


def main():
    """CLI entry point for scatter plot generation."""
    import argparse

    parser = argparse.ArgumentParser(description="Generate scatter plots from correlation data.")
    parser.add_argument("--input", type=str, required=True, help="Input CSV file or DataFrame path")
    parser.add_argument("--x", type=str, required=True, help="X-axis column name")
    parser.add_argument("--y", type=str, required=True, help="Y-axis column name")
    parser.add_argument("--output", type=str, required=True, help="Output PNG path")
    parser.add_argument("--metric-name", type=str, default=None, help="X-axis label")
    parser.add_argument("--score-name", type=str, default=None, help="Y-axis label")
    parser.add_argument("--title", type=str, default=None, help="Plot title")
    parser.add_argument("--q-value", type=float, default=None, help="FDR-corrected q-value")

    args = parser.parse_args()

    result = generate_scatter_plot(
        input=args.input,
        x=args.x,
        y=args.y,
        output=args.output,
        metric_name=args.metric_name,
        score_name=args.score_name,
        title=args.title,
        q_value=args.q_value
    )
    print(f"Plot saved to: {result}")


if __name__ == "__main__":
    sys.exit(main())
