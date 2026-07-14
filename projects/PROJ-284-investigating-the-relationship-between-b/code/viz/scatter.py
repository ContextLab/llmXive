"""Scatter plot generator for metric vs. score analysis.

Generates publication-quality scatter plots with regression lines,
confidence intervals, and annotated statistics (r, q).
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

from code.logging_config import get_logger

logger = get_logger(__name__)


def generate_scatter_plot(
    input: Optional[Union[str, Path, pd.DataFrame]] = None,
    x: Optional[str] = None,
    y: Optional[str] = None,
    output: Optional[Union[str, Path]] = None,
    title: Optional[str] = None,
    xlabel: Optional[str] = None,
    ylabel: Optional[str] = None,
    metric_name: Optional[str] = None,
    score_name: Optional[str] = None,
    regression_line: bool = True,
    confidence_interval: float = 0.95,
    show_r: bool = True,
    show_q: bool = True,
    color: str = "#2E86AB",
    point_alpha: float = 0.6,
    line_color: str = "#E94F37",
    line_width: float = 2.0,
    **kwargs: Any,
) -> Dict[str, Any]:
    """Generate a scatter plot with regression line and statistical annotations.

    This function supports multiple call signatures:
    1. Full keyword arguments: input, x, y, output
    2. DataFrame passed as first positional arg with x, y, output kwargs
    3. All arguments as kwargs (for **kwargs unpacking)

    Args:
        input: Path to CSV file or pandas DataFrame containing data
        x: Column name for x-axis (metric)
        y: Column name for y-axis (score)
        output: Output path for the figure (PNG/PDF)
        title: Plot title (auto-generated if None)
        xlabel: X-axis label (auto-generated if None)
        ylabel: Y-axis label (auto-generated if None)
        metric_name: Name of the metric for annotations
        score_name: Name of the score for annotations
        regression_line: Whether to show regression line
        confidence_interval: Confidence level for CI (0-1)
        show_r: Whether to show correlation coefficient
        show_q: Whether to show FDR-corrected p-value (q)
        color: Color for data points
        point_alpha: Alpha transparency for points
        line_color: Color for regression line
        line_width: Width of regression line
        **kwargs: Additional arguments (ignored for flexibility)

    Returns:
        Dictionary with plot statistics and file path:
        {
            'r': correlation coefficient,
            'p': p-value,
            'q': FDR-corrected p-value,
            'slope': regression slope,
            'intercept': regression intercept,
            'n_samples': number of data points,
            'output_path': path to saved figure
        }

    Raises:
        ValueError: If required arguments are missing or data is invalid
        FileNotFoundError: If input file doesn't exist
    """
    # Handle flexible call signatures
    if input is None and 'input' in kwargs:
        input = kwargs.pop('input')
    if x is None and 'x' in kwargs:
        x = kwargs.pop('x')
    if y is None and 'y' in kwargs:
        y = kwargs.pop('y')
    if output is None and 'output' in kwargs:
        output = kwargs.pop('output')

    # Validate required arguments
    if input is None:
        raise ValueError("Input data (path or DataFrame) is required")
    if x is None:
        raise ValueError("X-axis column name is required")
    if y is None:
        raise ValueError("Y-axis column name is required")

    # Load data
    if isinstance(input, (str, Path)):
        input_path = Path(input)
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")
        df = pd.read_csv(input_path)
    elif isinstance(input, pd.DataFrame):
        df = input.copy()
    else:
        raise TypeError(f"Input must be str, Path, or DataFrame, got {type(input)}")

    # Validate columns exist
    if x not in df.columns:
        raise ValueError(f"Column '{x}' not found in data. Available: {list(df.columns)}")
    if y not in df.columns:
        raise ValueError(f"Column '{y}' not found in data. Available: {list(df.columns)}")

    # Drop NaN values
    valid_mask = df[[x, y]].notna().all(axis=1)
    df_clean = df.loc[valid_mask]

    if len(df_clean) < 3:
        logger.log("scatter_plot_insufficient_data", n=len(df_clean), required=3)
        raise ValueError(f"Insufficient data points: {len(df_clean)} (need >= 3)")

    x_data = df_clean[x].values
    y_data = df_clean[y].values
    n = len(x_data)

    # Calculate statistics
    r, p, slope, intercept, std_err = stats.linregress(x_data, y_data)

    # Calculate FDR-corrected q-value (assuming single test for now)
    # In practice, this would come from the correlation analysis
    # For now, we assume q = p if not provided via kwargs
    q = p
    if 'q' in kwargs:
        q = kwargs['q']

    # Create figure
    fig, ax = plt.subplots(figsize=(10, 8))

    # Scatter plot
    ax.scatter(x_data, y_data, alpha=point_alpha, color=color, edgecolors='black', s=60)

    # Regression line
    if regression_line:
        x_line = np.linspace(x_data.min(), x_data.max(), 100)
        y_line = slope * x_line + intercept
        ax.plot(x_line, y_line, color=line_color, linewidth=line_width,
               label=f'Regression (r={r:.3f})')

        # Confidence interval band
        if confidence_interval > 0:
            t_val = stats.t.ppf((1 + confidence_interval) / 2, n - 2)
            # Standard error of the estimate
            y_pred = slope * x_line + intercept
            residuals = y_data - (slope * x_data + intercept)
            s_err = np.sqrt(np.sum(residuals**2) / (n - 2))
            # Confidence interval for the mean response
            x_mean = np.mean(x_data)
            denom = np.sqrt(np.sum((x_data - x_mean)**2))
            margin = t_val * s_err * np.sqrt(1/n + (x_line - x_mean)**2 / np.sum((x_data - x_mean)**2))
            ax.fill_between(x_line, y_pred - margin, y_pred + margin,
                           color=line_color, alpha=0.2, label=f'{confidence_interval*100:.0f}% CI')

    # Labels and title
    if title is None:
        if metric_name and score_name:
            title = f"{metric_name} vs. {score_name}"
        else:
            title = f"{y} vs. {x}"
    ax.set_title(title, fontsize=14, fontweight='bold')

    if xlabel is None:
        xlabel = metric_name if metric_name else x
    ax.set_xlabel(xlabel, fontsize=12)

    if ylabel is None:
        ylabel = score_name if score_name else y
    ax.set_ylabel(ylabel, fontsize=12)

    # Annotations
    annotation_text = []
    if show_r:
        annotation_text.append(f"r = {r:.3f}")
    if show_q:
        sig_marker = "*" if q < 0.05 else ""
        annotation_text.append(f"q = {q:.4f}{sig_marker}")
    annotation_text.append(f"N = {n}")

    annotation_str = "\n".join(annotation_text)
    ax.text(0.05, 0.95, annotation_str, transform=ax.transAxes,
           fontsize=11, verticalalignment='top',
           bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    # Grid and legend
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.legend(loc='best', fontsize=10)

    # Tight layout
    plt.tight_layout()

    # Save figure
    output_path = None
    if output:
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output_path, dpi=300, bbox_inches='tight')
        logger.log("scatter_plot_saved", path=str(output_path), n_samples=n, r=r, q=q)
    else:
        # If no output specified, return without saving
        logger.log("scatter_plot_generated", n_samples=n, r=r, q=q, saved=False)

    plt.close(fig)

    result = {
        'r': r,
        'p': p,
        'q': q,
        'slope': slope,
        'intercept': intercept,
        'n_samples': n,
        'output_path': str(output_path) if output_path else None,
    }

    return result


def main() -> None:
    """Main entry point for scatter plot generation.

    Reads correlation results from data/analysis/correlations.csv
    and generates scatter plots for each significant correlation.
    """
    logger.log("scatter_plot_main_start")

    # Default paths
    correlations_file = Path("data/analysis/correlations.csv")
    output_dir = Path("figures")

    if not correlations_file.exists():
        logger.log("correlations_file_missing", path=str(correlations_file))
        print(f"Error: Correlation results file not found: {correlations_file}")
        print("Please run the correlation analysis first (T024, T025)")
        return

    # Load correlation results
    corr_df = pd.read_csv(correlations_file)

    # Filter for significant correlations (q < 0.05)
    significant = corr_df[corr_df['significant'] == True]

    if significant.empty:
        logger.log("no_significant_correlations", total=len(corr_df))
        print("No significant correlations found to plot.")
        return

    logger.log("scatter_plot_processing", n_plots=len(significant))

    output_files = []

    for _, row in significant.iterrows():
        metric_name = row['metric_name']
        x_col = metric_name  # Assuming metric_name matches column in metrics data
        y_col = 'motor_score'  # Target variable

        # Load metrics data
        metrics_file = Path("data/processed/aggregated_metrics.csv")
        if not metrics_file.exists():
            logger.log("metrics_file_missing", path=str(metrics_file))
            print(f"Error: Metrics file not found: {metrics_file}")
            continue

        metrics_df = pd.read_csv(metrics_file)

        # Check if required columns exist
        if x_col not in metrics_df.columns or y_col not in metrics_df.columns:
            logger.log("columns_missing", metric=x_col, score=y_col, available=list(metrics_df.columns))
            continue

        # Generate plot
        output_path = output_dir / f"scatter_{metric_name.replace(' ', '_')}.png"

        try:
            result = generate_scatter_plot(
                input=metrics_df,
                x=x_col,
                y=y_col,
                output=str(output_path),
                metric_name=metric_name,
                score_name="Motor Score",
                q=row.get('q', row.get('p', 1.0)),  # Use q if available, else p
                show_r=True,
                show_q=True,
            )
            output_files.append(str(output_path))
            logger.log("scatter_plot_success", metric=metric_name, r=result['r'], q=result['q'])
        except Exception as e:
            logger.log("scatter_plot_error", metric=metric_name, error=str(e))
            print(f"Error generating plot for {metric_name}: {e}")

    logger.log("scatter_plot_main_complete", n_plots=len(output_files))
    print(f"Generated {len(output_files)} scatter plots in {output_dir}")


if __name__ == "__main__":
    main()