"""Scatter plot generation for correlation results.

Generates publication-quality scatter plots with regression lines,
annotated r and q values, and proper labeling.
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

from code.logging_config import get_logger

logger = get_logger(__name__)

# Ensure output directory exists
FIGURES_DIR = Path("figures")
FIGURES_DIR.mkdir(exist_ok=True)

def load_correlation_results(
    path: Optional[Union[str, Path]] = None
) -> pd.DataFrame:
    """Load correlation results from the analysis CSV.

    Args:
        path: Path to correlations.csv. If None, uses default location.

    Returns:
        DataFrame with correlation results including metric_name, r, p, q,
        significant, and subject data.
    """
    if path is None:
        path = Path("data/analysis/correlations.csv")
    else:
        path = Path(path)

    if not path.exists():
        logger.log("file_not_found", path=str(path), operation="load_correlation_results")
        raise FileNotFoundError(f"Correlation results file not found: {path}")

    df = pd.read_csv(path)
    logger.log("correlations_loaded", rows=len(df), operation="load_correlation_results")
    return df


def generate_scatter_plot(
    metric_name: str,
    score_col: str = "motor_score",
    output_path: Optional[Union[str, Path]] = None,
    data: Optional[pd.DataFrame] = None,
    correlation_results: Optional[pd.DataFrame] = None,
    **kwargs: Any
) -> str:
    """Generate a scatter plot for a specific metric vs motor score.

    Args:
        metric_name: Name of the metric column to plot on x-axis.
        score_col: Name of the score column to plot on y-axis (default: motor_score).
        output_path: Path to save the figure. If None, generates a default path.
        data: DataFrame containing the data. If None, loads from correlations.csv.
        correlation_results: DataFrame with correlation stats (r, p, q). If None,
                             computed from data.
        **kwargs: Additional plotting arguments.

    Returns:
        Path to the saved plot file
    """
    # Load data if not provided
    if data is None:
        try:
            data = load_correlation_results()
        except FileNotFoundError:
            # Try loading from full_metrics.csv as fallback
            fallback_path = Path("data/analysis/full_metrics.csv")
            if fallback_path.exists():
                data = pd.read_csv(fallback_path)
            else:
                raise FileNotFoundError(
                    "No data source found. Please run analysis first."
                )

    # Ensure metric exists
    if metric_name not in data.columns:
        raise ValueError(f"Metric '{metric_name}' not found in data. "
                       f"Available columns: {list(data.columns)}")

    # Filter out NaN values
    valid_mask = data[metric_name].notna() & data[score_col].notna()
    plot_data = data.loc[valid_mask, [metric_name, score_col]]

    if len(plot_data) < 2:
        raise ValueError(f"Insufficient data points for '{metric_name}' vs '{score_col}'")

    x = plot_data[metric_name].values
    y = plot_data[score_col].values

    # Compute correlation if not provided
    if correlation_results is None:
        r, p, _, _, _ = stats.pearsonr(x, y)
        q = p  # Placeholder for FDR-corrected value
        significant = p < 0.05
    else:
        # Look up in correlation_results
        row = correlation_results[correlation_results["metric_name"] == metric_name]
        if len(row) == 0:
            r, p, _, _, _ = stats.pearsonr(x, y)
            q = p
            significant = p < 0.05
        else:
            r = row["r"].iloc[0]
            p = row["p"].iloc[0]
            q = row["q"].iloc[0]
            significant = row["significant"].iloc[0]

    # Create figure
    fig, ax = plt.subplots(figsize=(10, 8))

    # Scatter plot
    ax.scatter(x, y, alpha=0.6, edgecolors='w', linewidth=0.5, s=80)

    # Add regression line
    if len(x) > 1:
        slope, intercept, r_val, p_val, std_err = stats.linregress(x, y)
        x_line = np.array([x.min(), x.max()])
        y_line = slope * x_line + intercept
        ax.plot(x_line, y_line, 'r-', linewidth=2, label=f'Regression (r={r_val:.3f})')

    # Annotate with r and q values
    annotation_text = (
        f"r = {r:.3f}\n"
        f"p = {p:.3g}\n"
        f"q (FDR) = {q:.3g}\n"
        f"{'Significant' if significant else 'Not significant'}"
    )
    ax.text(
        0.05, 0.95, annotation_text,
        transform=ax.transAxes,
        fontsize=11,
        verticalalignment='top',
        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5)
    )

    # Labels and title
    ax.set_xlabel(metric_name.replace('_', ' ').title(), fontsize=12)
    ax.set_ylabel(score_col.replace('_', ' ').title(), fontsize=12)
    ax.set_title(
        f"{metric_name.replace('_', ' ').title()} vs Motor Score",
        fontsize=14,
        fontweight='bold'
    )

    ax.grid(True, alpha=0.3)
    ax.legend(loc='lower right')

    # Determine output path
    if output_path is None:
        safe_name = metric_name.replace(' ', '_').replace('/', '_')
        output_path = FIGURES_DIR / f"{safe_name}_scatter.png"
    else:
        output_path = Path(output_path)

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Save figure
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close(fig)

    logger.log(
        "scatter_plot_generated",
        metric=metric_name,
        output=str(output_path),
        n_points=len(plot_data),
        r=r,
        p=p,
        q=q,
        operation="generate_scatter_plot"
    )

    return str(output_path)


def generate_all_scatter_plots(
    metrics: Optional[List[str]] = None,
    score_col: str = "motor_score",
    output_dir: Optional[Union[str, Path]] = None
) -> List[str]:
    """Generate scatter plots for all specified metrics.

    Args:
        metrics: List of metric names to plot. If None, uses common metrics.
        score_col: Column name for the score (y-axis).
        output_dir: Directory to save plots. If None, uses figures/.

    Returns:
        List of paths to generated plot files
    """
    if metrics is None:
        metrics = [
            'modularity',
            'global_efficiency',
            'participation_coef',
            'within_module_degree'
        ]

    if output_dir is None:
        output_dir = FIGURES_DIR
    else:
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)

    # Load correlation results for annotation
    try:
        correlation_results = load_correlation_results()
    except FileNotFoundError:
        correlation_results = None

    generated_files = []

    for metric in metrics:
        try:
            output_path = output_dir / f"{metric}_scatter.png"
            file_path = generate_scatter_plot(
                metric_name=metric,
                score_col=score_col,
                output_path=output_path,
                correlation_results=correlation_results
            )
            generated_files.append(file_path)
            logger.log("plot_generated", metric=metric, path=file_path)
        except Exception as e:
            logger.log(
                "plot_generation_failed",
                metric=metric,
                error=str(e),
                operation="generate_all_scatter_plots"
            )
            # Continue with other metrics

    logger.log(
        "all_plots_generated",
        count=len(generated_files),
        operation="generate_all_scatter_plots"
    )

    return generated_files


def main() -> None:
    """Main entry point for scatter plot generation.

    Generates scatter plots for all key metrics against motor scores.
    """
    logger.log("scatter_plot_main_start", operation="main")

    # Load data
    try:
        data = load_correlation_results()
    except FileNotFoundError:
        # Try alternative source
        alt_path = Path("data/analysis/full_metrics.csv")
        if alt_path.exists():
            data = pd.read_csv(alt_path)
        else:
            print("Error: No data source found. Run analysis first.")
            sys.exit(1)

    # Define metrics to plot
    metrics = [
        'modularity',
        'global_efficiency',
        'participation_coef',
        'within_module_degree'
    ]

    # Filter data to only include available metrics
    available_metrics = [m for m in metrics if m in data.columns]

    if not available_metrics:
        print(f"No metrics found in data. Available columns: {list(data.columns)}")
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


    print(f"Generating scatter plots for: {available_metrics}")

    # Generate all plots
    output_files = generate_all_scatter_plots(
        metrics=available_metrics,
        score_col="motor_score"
    )

    print(f"Generated {len(output_files)} scatter plots:")
    for f in output_files:
        print(f"  - {f}")

    logger.log("scatter_plot_main_complete", files=output_files, operation="main")


if __name__ == "__main__":
    main()