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

# Import logging utility (tolerant interface)
from code.logging_config import get_logger

logger = get_logger(__name__)

# Output directory for figures
FIGURES_DIR = Path("figures")
FIGURES_DIR.mkdir(exist_ok=True)

def load_correlation_results(
    path: Union[str, Path] = "data/analysis/correlation_results.csv"
) -> pd.DataFrame:
    """
    Load correlation results from CSV.
    Expected columns: metric_name, r, p, q, significant, covariate_controlled, subject_count (optional)
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Correlation results file not found: {path}")

    df = pd.read_csv(path)
    logger.log("load_correlation_results", path=str(path), rows=len(df))
    return df


def generate_scatter_plot(
    x: np.ndarray,
    y: np.ndarray,
    metric_name: str,
    score_name: str = "Motor Score",
    r: Optional[float] = None,
    p: Optional[float] = None,
    q: Optional[float] = None,
    output_path: Optional[Union[str, Path]] = None,
    title: Optional[str] = None,
    xlabel: Optional[str] = None,
    ylabel: Optional[str] = None,
    color: str = "#2C3E50",
    alpha: float = 0.7,
    show_plot: bool = False
) -> Path:
    """
    Generate a scatter plot with regression line and annotated statistics.

    Args:
        x: Independent variable data (e.g., network metric values)
        y: Dependent variable data (e.g., motor scores)
        metric_name: Name of the metric for the plot title/label
        score_name: Name of the score variable (default: "Motor Score")
        r: Pearson correlation coefficient (optional, computed if not provided)
        p: P-value (optional, computed if not provided)
        q: FDR-corrected q-value (optional)
        output_path: Path to save the figure. If None, auto-generated.
        title: Custom title. If None, auto-generated.
        xlabel: Custom X-axis label. If None, auto-generated.
        ylabel: Custom Y-axis label. If None, auto-generated.
        color: Color of data points and regression line.
        alpha: Transparency of data points.
        show_plot: If True, display the plot (for debugging).

    Returns:
        Path to the saved figure file.
    """
    x = np.asarray(x)
    y = np.asarray(y)

    if len(x) != len(y):
        raise ValueError(f"X and Y must have same length: {len(x)} vs {len(y)}")

    if len(x) < 2:
        raise ValueError("Need at least 2 data points to generate a scatter plot.")

    # Compute statistics if not provided
    if r is None or p is None:
        r, p = stats.pearsonr(x, y)

    # Create figure
    plt.style.use("seaborn-v0_8-whitegrid")
    fig, ax = plt.subplots(figsize=(10, 7))

    # Scatter plot
    ax.scatter(x, y, alpha=alpha, color=color, edgecolors="white", s=80, zorder=3)

    # Regression line
    if len(x) > 1:
        m, b, r_val, p_val, std_err = stats.linregress(x, y)
        x_line = np.linspace(x.min(), x.max(), 100)
        y_line = m * x_line + b
        ax.plot(x_line, y_line, color=color, linewidth=2.5, linestyle="-", zorder=2)

        # Add 95% confidence interval
        y_pred = m * x_line + b
        y_err = std_err * x_line + b  # Simplified CI calculation
        # More accurate CI for regression line:
        # SE_pred = std_err * np.sqrt(1/n + (x_line - x.mean())**2 / ((n-1)*x.var()))
        # But for simplicity and visual clarity, we use a band:
        ax.fill_between(
            x_line,
            y_pred - 1.96 * std_err,
            y_pred + 1.96 * std_err,
            color=color,
            alpha=0.15,
            zorder=1
        )

    # Labels and Title
    if title is None:
        title = f"{metric_name} vs. {score_name}"
    if xlabel is None:
        xlabel = metric_name
    if ylabel is None:
        ylabel = score_name

    ax.set_title(title, fontsize=16, fontweight="bold", pad=15)
    ax.set_xlabel(xlabel, fontsize=12, fontweight="medium")
    ax.set_ylabel(ylabel, fontsize=12, fontweight="medium")

    # Annotate statistics
    stat_text = []
    stat_text.append(f"r = {r:.3f}")
    stat_text.append(f"p = {p:.3e}" if p < 1e-3 else f"p = {p:.3f}")
    if q is not None:
        sig_marker = "*" if q < 0.05 else ""
        stat_text.append(f"q = {q:.3f}{sig_marker}")

    stats_str = "\n".join(stat_text)

    # Position annotation in top-left
    props = dict(boxstyle="round", facecolor="white", alpha=0.8, edgecolor="gray")
    ax.text(
        0.05, 0.95, stats_str,
        transform=ax.transAxes,
        fontsize=11,
        verticalalignment="top",
        fontfamily="monospace",
        bbox=props
    )

    # Grid
    ax.grid(True, linestyle="--", alpha=0.6)

    # Tight layout
    plt.tight_layout()

    # Save figure
    if output_path is None:
        safe_name = metric_name.replace(" ", "_").replace("/", "_").lower()
        output_path = FIGURES_DIR / f"scatter_{safe_name}.png"
    else:
        output_path = Path(output_path)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)

    logger.log(
        "generate_scatter_plot",
        output=str(output_path),
        n_points=len(x),
        r=r,
        p=p,
        q=q
    )

    if show_plot:
        plt.show()

    return output_path


def generate_all_scatter_plots(
    results_df: Optional[pd.DataFrame] = None,
    metrics_data: Optional[pd.DataFrame] = None,
    score_column: str = "motor_score",
    output_dir: Optional[Union[str, Path]] = None
) -> List[Path]:
    """
    Generate scatter plots for all significant correlations in the results.

    Args:
        results_df: DataFrame with correlation results (metric_name, r, p, q, significant).
        metrics_data: DataFrame with raw metric values and scores (columns: metric_name, score_column).
        score_column: Name of the score column in metrics_data.
        output_dir: Directory to save plots. Defaults to FIGURES_DIR.

    Returns:
        List of paths to generated figure files.
    """
    if results_df is None:
        try:
            results_df = load_correlation_results()
        except FileNotFoundError:
            logger.log("generate_all_scatter_plots", error="No correlation results found")
            return []

    if output_dir is None:
        output_dir = FIGURES_DIR
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)

    generated_paths = []

    for _, row in results_df.iterrows():
        metric_name = row["metric_name"]
        r = row["r"]
        p = row["p"]
        q = row.get("q", None)
        significant = row.get("significant", False)

        # Skip if no significant correlation or if data is missing
        # (Optional: generate plots for all, not just significant)
        if pd.isna(r) or pd.isna(p):
            continue

        if metrics_data is not None and metric_name in metrics_data.columns:
            x = metrics_data[metric_name].dropna()
            # Align y with x
            y = metrics_data.loc[x.index, score_column].dropna()
            # Re-align indices after dropna
            common_idx = x.index.intersection(y.index)
            x = x.loc[common_idx]
            y = y.loc[common_idx]

            if len(x) < 2:
                continue

            try:
                path = generate_scatter_plot(
                    x=x.values,
                    y=y.values,
                    metric_name=metric_name,
                    score_name="Motor Score",
                    r=r,
                    p=p,
                    q=q,
                    title=f"{metric_name} vs. Motor Performance"
                )
                generated_paths.append(path)
                logger.log("generate_all_scatter_plots", metric=metric_name, path=str(path))
            except Exception as e:
                logger.log("generate_all_scatter_plots", metric=metric_name, error=str(e))
        else:
            # If raw data not provided, we cannot generate the plot
            # This is expected if only summary stats are available
            logger.log(
                "generate_all_scatter_plots",
                metric=metric_name,
                status="skipped",
                reason="raw_data_missing"
            )

    return generated_paths


def main() -> None:
    """
    Main entry point for scatter plot generation.
    Loads correlation results and metric data, then generates plots.
    """
    logger.log("scatter_main", status="starting")

    # Load correlation results
    try:
        results_df = load_correlation_results("data/analysis/correlation_results.csv")
    except FileNotFoundError:
        logger.log("scatter_main", status="failed", reason="correlation_results_not_found")
        print("Error: data/analysis/correlation_results.csv not found.")
        print("Please run the correlation analysis (T024/T025) first.")
        sys.exit(1)

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
