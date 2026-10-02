"""
Visualization module for generating diagnostic plots.

This module creates scatter plots with regression lines and residual diagnostic plots.
"""

import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import os
import logging

from utils.logger import get_logger, log_pipeline_step

logger = get_logger(__name__)


def create_scatter_plot(
    data: pd.DataFrame,
    x_col: str = "psv_score",
    y_col: str = "self_perception_score",
    output_path: str = "scatter_plot.png",
    title: str = "Perceived Social Validation vs Self-Perception"
) -> None:
    """
    Create a scatter plot with a regression line.

    Args:
        data: Input DataFrame.
        x_col: Column name for the x-axis.
        y_col: Column name for the y-axis.
        output_path: Path to save the plot.
        title: Plot title.
    """
    log_pipeline_step("Creating scatter plot")

    # Filter valid data
    mask = data[[x_col, y_col]].notna().all(axis=1)
    x = data.loc[mask, x_col]
    y = data.loc[mask, y_col]

    if len(x) == 0:
        logger.warning("No valid data for scatter plot.")
        return

    plt.figure(figsize=(10, 6))
    plt.scatter(x, y, alpha=0.6, edgecolors='k')

    # Add regression line
    z = np.polyfit(x, y, 1)
    p = np.poly1d(z)
    plt.plot(x, p(x), "r-", label=f"y = {z[0]:.2f}x + {z[1]:.2f}")

    plt.xlabel(x_col)
    plt.ylabel(y_col)
    plt.title(title)
    plt.legend()
    plt.grid(True, alpha=0.3)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()

    logger.info(f"Scatter plot saved to {output_path}")


def create_residual_plot(
    data: pd.DataFrame,
    x_col: str = "psv_score",
    y_col: str = "self_perception_score",
    output_path: str = "residuals.png",
    title: str = "Residual Diagnostics"
) -> None:
    """
    Create a residual diagnostic plot.

    Args:
        data: Input DataFrame.
        x_col: Column name for the predictor.
        y_col: Column name for the outcome.
        output_path: Path to save the plot.
        title: Plot title.
    """
    log_pipeline_step("Creating residual plot")

    # Filter valid data
    mask = data[[x_col, y_col]].notna().all(axis=1)
    x = data.loc[mask, x_col]
    y = data.loc[mask, y_col]

    if len(x) == 0:
        logger.warning("No valid data for residual plot.")
        return

    # Fit simple linear regression for residuals
    z = np.polyfit(x, y, 1)
    p = np.poly1d(z)
    y_pred = p(x)
    residuals = y - y_pred

    plt.figure(figsize=(10, 6))
    plt.scatter(y_pred, residuals, alpha=0.6, edgecolors='k')
    plt.axhline(0, color='red', linestyle='--')

    plt.xlabel("Predicted Values")
    plt.ylabel("Residuals")
    plt.title(title)
    plt.grid(True, alpha=0.3)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()

    logger.info(f"Residual plot saved to {output_path}")


def run_viz_pipeline(
    data: pd.DataFrame,
    output_dir: str = "data/processed"
) -> dict:
    """
    Run the full visualization pipeline.

    Args:
        data: Input DataFrame.
        output_dir: Directory to save plots.

    Returns:
        Dictionary with paths to generated plots.
    """
    log_pipeline_step("Starting visualization pipeline")

    scatter_path = os.path.join(output_dir, "scatter_plot.png")
    residual_path = os.path.join(output_dir, "residuals.png")

    create_scatter_plot(data, output_path=scatter_path)
    create_residual_plot(data, output_path=residual_path)

    return {
        "scatter_plot": scatter_path,
        "residual_plot": residual_path
    }


def main() -> None:
    """
    Main entry point for visualization module.
    """
    from pathlib import Path
    base_dir = Path(__file__).resolve().parents[2]
    data_path = base_dir / "data" / "processed" / "pipeline_data.csv"
    output_dir = str(base_dir / "data" / "processed")

    logger.info("Executing main() for viz pipeline")

    if not data_path.exists():
        logger.error(f"Data file not found: {data_path}")
        return

    logger.info(f"Loading data from {data_path}")
    df = pd.read_csv(data_path)

    run_viz_pipeline(df, output_dir)


if __name__ == "__main__":
    main()
