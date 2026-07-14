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

# Project imports
from code.logging_config import get_logger
from code.analysis.correlations import apply_fdr_correction, run_correlations_with_fd_covariate

logger = get_logger(__name__)

# Constants
FIGURE_DPI = 300
FIGURE_SIZE = (10, 8)
FONT_SIZE = 12
LABEL_SIZE = 14
TITLE_SIZE = 16
OUTPUT_DIR = Path("data/analysis")
FIGURES_DIR = Path("figures")

# Ensure output directories exist
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
FIGURES_DIR.mkdir(parents=True, exist_ok=True)


def load_correlation_results(
    filepath: Optional[Union[str, Path]] = None
) -> pd.DataFrame:
    """
    Load correlation results from CSV.

    Args:
        filepath: Path to the correlation results CSV. Defaults to
                 'data/analysis/correlations.csv'.

    Returns:
        DataFrame with correlation results.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    if filepath is None:
        filepath = OUTPUT_DIR / "correlations.csv"
    else:
        filepath = Path(filepath)

    if not filepath.exists():
        raise FileNotFoundError(f"Correlation results file not found: {filepath}")

    logger.log("load_correlation_results", path=str(filepath))
    df = pd.read_csv(filepath)
    logger.log("correlation_results_loaded", rows=len(df))
    return df


def generate_scatter_plot(
    x_data: Union[np.ndarray, List[float], pd.Series],
    y_data: Union[np.ndarray, List[float], pd.Series],
    metric_name: str,
    score_name: str,
    correlation_result: Optional[Dict[str, Any]] = None,
    output_path: Optional[Union[str, Path]] = None,
    title: Optional[str] = None,
    x_label: Optional[str] = None,
    y_label: Optional[str] = None,
    show_plot: bool = False,
) -> Path:
    """
    Generate a scatter plot with regression line and annotated statistics.

    Args:
        x_data: Independent variable data.
        y_data: Dependent variable data.
        metric_name: Name of the metric (for filename and label).
        score_name: Name of the score/behavioral measure.
        correlation_result: Optional dict with 'r', 'p', 'q' keys for annotation.
        output_path: Path to save the figure. If None, auto-generated based on
                    metric_name and score_name.
        title: Optional custom title.
        x_label: Optional custom x-axis label.
        y_label: Optional custom y-axis label.
        show_plot: Whether to display the plot (useful for debugging).

    Returns:
        Path to the saved figure file.

    Raises:
        ValueError: If input data lengths don't match.
    """
    # Convert inputs to numpy arrays for consistency
    x = np.asarray(x_data)
    y = np.asarray(y_data)

    if len(x) != len(y):
        raise ValueError(
            f"x_data and y_data must have the same length. "
            f"Got {len(x)} and {len(y)}."
        )

    if len(x) < 2:
        raise ValueError("Need at least 2 data points to generate a scatter plot.")

    # Auto-generate output path if not provided
    if output_path is None:
        safe_metric = metric_name.replace(" ", "_").replace("/", "_").lower()
        safe_score = score_name.replace(" ", "_").replace("/", "_").lower()
        output_path = FIGURES_DIR / f"scatter_{safe_metric}_vs_{safe_score}.png"
    else:
        output_path = Path(output_path)

    # Create figure and axis
    fig, ax = plt.subplots(figsize=FIGURE_SIZE, dpi=FIGURE_DPI)

    # Scatter plot
    ax.scatter(x, y, alpha=0.7, edgecolors='k', linewidth=0.5, s=60, zorder=3)

    # Calculate and plot regression line
    if len(x) >= 2:
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
        x_line = np.linspace(min(x), max(x), 100)
        y_line = slope * x_line + intercept
        ax.plot(x_line, y_line, 'r-', linewidth=2, label=f'Regression (r={r_value:.3f})', zorder=2)

        # Add 95% confidence interval shading
        y_pred = slope * x + intercept
        residuals = y - y_pred
        se_line = std_err * np.sqrt(1/len(x) + (x_line - np.mean(x))**2 / np.sum((x - np.mean(x))**2))
        ax.fill_between(x_line, y_line - 1.96 * se_line, y_line + 1.96 * se_line,
                       color='red', alpha=0.2, label='95% CI')

    # Set labels and title
    if title is None:
        title = f"{metric_name} vs. {score_name}"
    ax.set_title(title, fontsize=TITLE_SIZE, fontweight='bold')

    if x_label is None:
        x_label = metric_name
    ax.set_xlabel(x_label, fontsize=LABEL_SIZE)

    if y_label is None:
        y_label = score_name
    ax.set_ylabel(y_label, fontsize=LABEL_SIZE)

    # Add correlation statistics annotation
    if correlation_result:
        r = correlation_result.get('r', r_value if len(x) >= 2 else None)
        p = correlation_result.get('p', p_value if len(x) >= 2 else None)
        q = correlation_result.get('q', None)

        annotation_parts = []
        if r is not None:
            annotation_parts.append(f"r = {r:.3f}")
        if p is not None:
            sig_marker = "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else "ns"
            annotation_parts.append(f"p = {p:.3f} {sig_marker}")
        if q is not None:
            annotation_parts.append(f"q (FDR) = {q:.3f}")

        annotation_text = "\n".join(annotation_parts)

        # Position annotation in upper right
        ax.annotate(
            annotation_text,
            xy=(0.98, 0.98),
            xycoords='axes fraction',
            horizontalalignment='right',
            verticalalignment='top',
            bbox=dict(boxstyle="round,pad=0.5", facecolor="white", alpha=0.8, edgecolor="gray"),
            fontsize=FONT_SIZE,
            fontfamily='monospace'
        )

    # Add grid
    ax.grid(True, linestyle='--', alpha=0.5, zorder=1)

    # Adjust layout
    plt.tight_layout()

    # Save figure
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=FIGURE_DPI, bbox_inches='tight')
    plt.close(fig)

    logger.log(
        "scatter_plot_generated",
        metric=metric_name,
        score=score_name,
        output=str(output_path),
        n_points=len(x),
        r=r if len(x) >= 2 else None
    )

    if show_plot:
        plt.show()

    return output_path


def generate_all_scatter_plots(
    correlations_df: Optional[pd.DataFrame] = None,
    metrics_df: Optional[pd.DataFrame] = None,
    output_dir: Optional[Union[str, Path]] = None,
) -> List[Path]:
    """
    Generate scatter plots for all significant correlations.

    Args:
        correlations_df: DataFrame with correlation results. If None, loads from
                       default location.
        metrics_df: DataFrame with metric values. If None, attempts to load from
                   'data/analysis/full_metrics.csv'.
        output_dir: Directory to save plots. Defaults to 'figures/'.

    Returns:
        List of paths to generated figure files.
    """
    if output_dir is None:
        output_dir = FIGURES_DIR
    else:
        output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load correlation results if not provided
    if correlations_df is None:
        try:
            correlations_df = load_correlation_results()
        except FileNotFoundError as e:
            logger.log("generate_all_scatter_plots_error", error=str(e))
            return []

    # Load metrics data if not provided
    if metrics_df is None:
        metrics_path = Path("data/analysis/full_metrics.csv")
        if metrics_path.exists():
            metrics_df = pd.read_csv(metrics_path)
        else:
            logger.log("generate_all_scatter_plots_warning",
                     message="full_metrics.csv not found, plots will use correlation data only")
            metrics_df = None

    generated_plots = []

    # Iterate through significant correlations
    significant = correlations_df[correlations_df['significant'] == True]

    for idx, row in significant.iterrows():
        metric_name = row['metric_name']
        r = row['r']
        p = row['p']
        q = row['q']

        correlation_result = {'r': r, 'p': p, 'q': q}

        # Try to get actual data points if metrics_df is available
        x_data = None
        y_data = None

        if metrics_df is not None and metric_name in metrics_df.columns:
            x_data = metrics_df[metric_name].dropna()
            # Assume motor_score or similar is in the dataframe
            score_col = [col for col in metrics_df.columns if 'motor' in col.lower() or 'score' in col.lower()]
            if score_col:
                y_data = metrics_df[score_col[0]].dropna()
                # Align x and y
                common_idx = x_data.index.intersection(y_data.index)
                x_data = x_data.loc[common_idx]
                y_data = y_data.loc[common_idx]

        if x_data is not None and len(x_data) >= 2:
            try:
                plot_path = generate_scatter_plot(
                    x_data=x_data,
                    y_data=y_data,
                    metric_name=metric_name,
                    score_name="Motor Score",
                    correlation_result=correlation_result,
                    output_path=output_dir / f"scatter_{metric_name.replace(' ', '_').lower()}.png",
                )
                generated_plots.append(plot_path)
                logger.log("plot_saved", path=str(plot_path))
            except Exception as e:
                logger.log("plot_generation_failed", metric=metric_name, error=str(e))
        else:
            # Fallback: generate a placeholder plot if data not available
            # This should not happen in production with real data
            logger.log("plot_skipped_no_data", metric=metric_name)

    logger.log("all_plots_generated", count=len(generated_plots))
    return generated_plots


def main() -> None:
    """
    Main entry point for scatter plot generation.
    Loads correlation results and generates plots for all significant findings.
    """
    logger.log("scatter_plot_main_started")

    try:
        # Load correlation results
        correlations_df = load_correlation_results()

        # Generate all plots
        plots = generate_all_scatter_plots(correlations_df)

        print(f"Generated {len(plots)} scatter plots in {FIGURES_DIR}")
        for p in plots:
            print(f"  - {p}")

        logger.log("scatter_plot_main_completed", num_plots=len(plots))

    except FileNotFoundError as e:
        logger.log("scatter_plot_main_error", error=str(e))
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.log("scatter_plot_main_unexpected_error", error=str(e))
        print(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()