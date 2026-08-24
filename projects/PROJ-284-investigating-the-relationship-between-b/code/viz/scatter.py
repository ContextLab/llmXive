from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

from code.logging_config import get_logger

logger = get_logger(__name__)


def load_correlation_results(path: Path) -> pd.DataFrame:
    """Loads correlation results produced by the analysis pipeline."""
    if not path.exists():
        logger.log(
            "load_correlation_results",
            status="failed",
            reason=f"File not found: {path}",
        )
        raise FileNotFoundError(f"Correlation results file not found: {path}")
    return pd.read_csv(path)


def generate_scatter_plot(
    data: pd.DataFrame,
    x_col: str,
    y_col: str,
    output_path: Path,
    title: str = "Scatter Plot",
    r: Optional[float] = None,
    q: Optional[float] = None,
    **kwargs,
) -> None:
    """
    Generates a scatter plot with a linear regression line.

    Parameters
    ----------
    data : pd.DataFrame
        Dataframe containing the data to plot.
    x_col : str
        Column name for the x‑axis (typically a network metric).
    y_col : str
        Column name for the y‑axis (typically the behavioural score).
    output_path : Path
        Destination file for the PNG image.
    title : str, optional
        Plot title.
    r : float, optional
        Pearson/Spearman correlation coefficient to annotate.
    q : float, optional
        FDR‑corrected q‑value to annotate.
    **kwargs
        Additional keyword arguments (currently ignored but kept for API stability).
    """
    logger.log(
        "generate_scatter_plot",
        x=x_col,
        y=y_col,
        output=str(output_path),
        r=r,
        q=q,
    )

    # Defensive copy to avoid mutating caller data
    plot_data = data[[x_col, y_col]].dropna()

    if plot_data.empty:
        logger.log(
            "generate_scatter_plot",
            status="skipped",
            reason="No data after dropping NaNs",
        )
        return

    plt.figure(figsize=(8, 6))
    plt.scatter(plot_data[x_col], plot_data[y_col], alpha=0.7, edgecolor="k")

    # Linear regression line (least‑squares)
    try:
        coeffs = np.polyfit(plot_data[x_col], plot_data[y_col], 1)
        poly = np.poly1d(coeffs)
        x_vals = np.linspace(plot_data[x_col].min(), plot_data[x_col].max(), 100)
        plt.plot(x_vals, poly(x_vals), "r--", linewidth=2)
    except Exception as exc:  # pragma: no cover – extremely unlikely
        logger.log(
            "generate_scatter_plot",
            status="warning",
            reason=f"Regression failed: {exc}",
        )

    plt.xlabel(x_col)
    plt.ylabel(y_col)
    plt.title(title)

    # Annotate statistical values if supplied
    if r is not None and q is not None:
        plt.text(
            0.05,
            0.95,
            f"r = {r:.2f}\\nq = {q:.3f}",
            transform=plt.gca().transAxes,
            verticalalignment="top",
            bbox=dict(facecolor="white", alpha=0.7, edgecolor="none"),
        )

    # Ensure parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()

    logger.log("generate_scatter_plot", status="success", output=str(output_path))


def generate_all_scatter_plots(results_path: Path, output_dir: Path) -> None:
    """
    Generates scatter plots for every significant correlation.

    The function expects ``results_path`` to point to the FDR‑corrected
    correlation results CSV (produced by ``code/analysis/correlations.py``)
    and a companion file ``data/analysis/full_metrics.csv`` that contains
    per‑subject metric values together with the behavioural score
    (``motor_score``). For each significant metric a plot of
    ``metric`` vs. ``motor_score`` is saved as ``{metric}_vs_motor_score.png``.
    """
    logger.log(
        "generate_all_scatter_plots",
        results_path=str(results_path),
        output_dir=str(output_dir),
    )

    if not results_path.exists():
        logger.log(
            "generate_all_scatter_plots",
            status="skipped",
            reason="Results file not found",
        )
        return

    # Load correlation results
    corr_df = load_correlation_results(results_path)

    # Keep only rows marked as significant (boolean column expected)
    if "significant" not in corr_df.columns:
        logger.log(
            "generate_all_scatter_plots",
            status="failed",
            reason="Column 'significant' missing in results",
        )
        raise KeyError("Column 'significant' missing in correlation results")

    sig_df = corr_df[corr_df["significant"]].copy()
    if sig_df.empty:
        logger.log(
            "generate_all_scatter_plots",
            status="skipped",
            reason="No significant correlations found",
        )
        return

    # Load the full per‑subject metrics (must contain the behavioural score)
    full_metrics_path = Path("data/analysis/full_metrics.csv")
    if not full_metrics_path.exists():
        logger.log(
            "generate_all_scatter_plots",
            status="failed",
            reason=f"Full metrics file not found: {full_metrics_path}",
        )
        raise FileNotFoundError(f"Full metrics file not found: {full_metrics_path}")

    full_df = pd.read_csv(full_metrics_path)

    # The behavioural score column name is not hard‑coded in the spec.
    # We try a few common possibilities.
    possible_score_cols = ["motor_score", "score", "behaviour_score"]
    score_col = next(
        (col for col in possible_score_cols if col in full_df.columns), None
    )
    if score_col is None:
        logger.log(
            "generate_all_scatter_plots",
            status="failed",
            reason="Behavioural score column not found in full_metrics.csv",
        )
        raise KeyError(
            "Behavioural score column not found in full_metrics.csv"
        )

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    for _, row in sig_df.iterrows():
        metric_name = row["metric"] if "metric" in row else row.get("metric_name")
        if not metric_name:
            logger.log(
                "generate_all_scatter_plots",
                status="warning",
                reason="Row missing metric identifier; skipping",
            )
            continue

        if metric_name not in full_df.columns:
            logger.log(
                "generate_all_scatter_plots",
                status="warning",
                reason=f"Metric column '{metric_name}' not present in full_metrics.csv",
            )
            continue

        # Prepare data for the plot
        plot_df = full_df[[metric_name, score_col]].dropna()
        if plot_df.empty:
            logger.log(
                "generate_all_scatter_plots",
                status="warning",
                reason=f"No data for metric '{metric_name}' after dropping NaNs",
            )
            continue

        # Extract statistical annotations from the correlation row
        r_val = float(row["r"]) if "r" in row else None
        q_val = float(row["q"]) if "q" in row else None

        title = f"{metric_name} vs. {score_col}"
        out_path = output_dir / f"{metric_name}_vs_{score_col}.png"

        generate_scatter_plot(
            data=plot_df,
            x_col=metric_name,
            y_col=score_col,
            output_path=out_path,
            title=title,
            r=r_val,
            q=q_val,
        )

    logger.log("generate_all_scatter_plots", status="completed")


def main() -> None:
    """
    Entry‑point used by the quick‑start run‑book.

    Expected locations (relative to the project root):
    - Correlation results: ``data/analysis/fdr_corrected_results.csv``
    - Output directory: ``figures/scatter_plots``
    """
    results_path = Path("data/analysis/fdr_corrected_results.csv")
    output_dir = Path("figures/scatter_plots")
    generate_all_scatter_plots(results_path, output_dir)


if __name__ == "__main__":
    # Allow direct execution for debugging / ad‑hoc runs
    main()