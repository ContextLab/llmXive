import os
import logging
import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Any

from code.config import Config
from code.utils.logging import setup_logging

logger = logging.getLogger(__name__)


def generate_scatter_plot(
    x: np.ndarray,
    y: np.ndarray,
    x_label: str,
    y_label: str,
    title: str,
    output_path: Path,
    regression_line: bool = True
) -> None:
    """
    Generate a scatter plot with an optional regression line.

    Args:
        x: 1D array of x-values.
        y: 1D array of y-values.
        x_label: Label for the x-axis.
        y_label: Label for the y-axis.
        title: Title of the plot.
        output_path: Path to save the figure.
        regression_line: Whether to plot a linear regression line.
    """
    plt.figure(figsize=(8, 6))
    plt.scatter(x, y, alpha=0.7, edgecolors='k')

    if regression_line:
        # Simple linear regression
        m, b = np.polyfit(x, y, 1)
        plt.plot(x, m * x + b, 'r-', label=f'y = {m:.2f}x + {b:.2f}')
        plt.legend()

    plt.xlabel(x_label)
    plt.ylabel(y_label)
    plt.title(title)
    plt.grid(True, alpha=0.3)

    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300)
    plt.close()
    logger.info(f"Scatter plot saved to {output_path}")


def generate_regression_line_plot(
    x: np.ndarray,
    y: np.ndarray,
    x_label: str,
    y_label: str,
    title: str,
    output_path: Path,
    model=None
) -> None:
    """
    Generate a plot showing data points and a fitted regression line.

    Args:
        x: 1D array of x-values.
        y: 1D array of y-values.
        x_label: Label for the x-axis.
        y_label: Label for the y-axis.
        title: Title of the plot.
        output_path: Path to save the figure.
        model: Optional fitted model object to use for prediction.
    """
    plt.figure(figsize=(8, 6))
    plt.scatter(x, y, alpha=0.7, edgecolors='k', label='Data')

    if model is not None:
        # Assume model has predict method
        x_sorted = np.sort(x)
        y_pred = model.predict(x_sorted.reshape(-1, 1))
        plt.plot(x_sorted, y_pred, 'r-', label='Fitted Line')
        plt.legend()
    else:
        # Fallback to simple polyfit
        m, b = np.polyfit(x, y, 1)
        x_sorted = np.sort(x)
        plt.plot(x_sorted, m * x_sorted + b, 'r-', label='Simple Fit')
        plt.legend()

    plt.xlabel(x_label)
    plt.ylabel(y_label)
    plt.title(title)
    plt.grid(True, alpha=0.3)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300)
    plt.close()
    logger.info(f"Regression line plot saved to {output_path}")


def generate_residual_plot(
    x: np.ndarray,
    residuals: np.ndarray,
    title: str,
    output_path: Path
) -> None:
    """
    Generate a residual plot to check model assumptions.

    Args:
        x: 1D array of x-values (predicted or independent variable).
        residuals: 1D array of residual values.
        title: Title of the plot.
        output_path: Path to save the figure.
    """
    plt.figure(figsize=(8, 6))
    plt.scatter(x, residuals, alpha=0.7, edgecolors='k')
    
    # Add a horizontal line at y=0
    plt.axhline(y=0, color='r', linestyle='--', linewidth=1)

    plt.xlabel("Predicted Values / Independent Variable")
    plt.ylabel("Residuals")
    plt.title(title)
    plt.grid(True, alpha=0.3)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300)
    plt.close()
    logger.info(f"Residual plot saved to {output_path}")


def run_analysis(
    results_df: pd.DataFrame,
    output_dir: Path,
    config: Config
) -> None:
    """
    Run the plotting analysis pipeline.

    Args:
        results_df: DataFrame containing statistical results.
        output_dir: Path to save plots.
        config: Configuration object.
    """
    ensure_directories(output_dir)
    
    # Example: Plot Post vs Pre treatment scores
    if 'pre_treatment_score' in results_df.columns and 'post_treatment_score' in results_df.columns:
        x = results_df['pre_treatment_score'].values
        y = results_df['post_treatment_score'].values
        
        generate_scatter_plot(
            x, y,
            "Pre-Treatment Score",
            "Post-Treatment Score",
            "Pre vs Post Treatment Scores",
            output_dir / "pre_post_scatter.png"
        )

    # Example: Plot Metric vs Post Treatment
    if 'network_metric' in results_df.columns and 'post_treatment_score' in results_df.columns:
        x = results_df['network_metric'].values
        y = results_df['post_treatment_score'].values
        
        generate_regression_line_plot(
            x, y,
            "Network Metric",
            "Post-Treatment Score",
            "Network Metric vs Post-Treatment Score",
            output_dir / "metric_vs_post.png"
        )

    logger.info("Plotting analysis complete.")


def ensure_directories(path: Path) -> None:
    """Ensure the given path exists, creating it if necessary."""
    path.mkdir(parents=True, exist_ok=True)


def main():
    """Main entry point for the plotting script."""
    setup_logging()
    config = Config()
    
    # Load results (simplified)
    results_path = Path(config.metrics_output_dir) / "statistical_results.csv"
    if results_path.exists():
        df = pd.read_csv(results_path)
        run_analysis(df, Path(config.figures_output_dir), config)
    else:
        logger.warning(f"Results file not found: {results_path}")


if __name__ == "__main__":
    main()
