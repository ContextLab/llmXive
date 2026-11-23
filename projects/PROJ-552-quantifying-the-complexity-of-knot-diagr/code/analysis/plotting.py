"""
Plotting Module for Knot Complexity Analysis.

This module handles all figure generation logic, including scatter plots,
residual plots, and model comparison plots.
"""
from __future__ import annotations

import pathlib
from pathlib import Path
from typing import Any, Dict, List, Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from code.reproducibility.logs import get_logger, log_operation

logger = get_logger(__name__)

# Set style
sns.set(style="whitegrid")


@log_operation
def create_scatter_plot(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    title: str,
    x_label: str,
    y_label: str,
    output_path: Path,
    hue_col: Optional[str] = None
) -> None:
    """
    Create a scatter plot of x vs y.

    Args:
        df: DataFrame containing the data.
        x_col: Column name for x-axis.
        y_col: Column name for y-axis.
        title: Plot title.
        x_label: X-axis label.
        y_label: Y-axis label.
        output_path: Path to save the plot.
        hue_col: Optional column for coloring points.
    """
    plt.figure(figsize=(10, 6))
    if hue_col:
        sns.scatterplot(data=df, x=x_col, y=y_col, hue=hue_col, alpha=0.7)
    else:
        sns.scatterplot(data=df, x=x_col, y=y_col, alpha=0.7)

    plt.title(title)
    plt.xlabel(x_label)
    plt.ylabel(y_label)
    plt.tight_layout()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300)
    plt.close()

    logger.log("scatter_plot_created", parameters={"path": str(output_path), "x": x_col, "y": y_col})


@log_operation
def create_residual_plot(
    residuals: List[float],
    predicted: List[float],
    title: str,
    output_path: Path
) -> None:
    """
    Create a residual plot (residuals vs predicted).

    Args:
        residuals: List of residual values.
        predicted: List of predicted values.
        title: Plot title.
        output_path: Path to save the plot.
    """
    plt.figure(figsize=(10, 6))
    plt.scatter(predicted, residuals, alpha=0.7)
    plt.axhline(0, color='red', linestyle='--', linewidth=1)

    plt.title(title)
    plt.xlabel("Predicted Values")
    plt.ylabel("Residuals")
    plt.tight_layout()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300)
    plt.close()

    logger.log("residual_plot_created", parameters={"path": str(output_path)})


@log_operation
def create_model_comparison_plot(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    models: List[Dict[str, Any]],
    output_path: Path
) -> None:
    """
    Create a plot comparing multiple regression models.

    Args:
        df: DataFrame containing the data.
        x_col: Column name for x-axis.
        y_col: Column name for y-axis.
        models: List of model dictionaries containing 'name', 'func', 'color'.
        output_path: Path to save the plot.
    """
    plt.figure(figsize=(10, 6))
    plt.scatter(df[x_col], df[y_col], alpha=0.5, label="Data", color='black')

    x_sorted = np.sort(df[x_col].unique())

    for model in models:
        name = model.get("name", "Model")
        func = model.get("func")
        color = model.get("color", "blue")
        if func and x_sorted.size > 0:
            y_pred = func(x_sorted)
            plt.plot(x_sorted, y_pred, label=name, color=color, linewidth=2)

    plt.title(f"Model Comparison: {y_col} vs {x_col}")
    plt.xlabel(x_col)
    plt.ylabel(y_col)
    plt.legend()
    plt.tight_layout()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300)
    plt.close()

    logger.log("model_comparison_plot_created", parameters={"path": str(output_path), "models": len(models)})


@log_operation
def create_stratified_scatter_plot(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    strat_col: str,
    title: str,
    output_path: Path
) -> None:
    """
    Create a scatter plot stratified by a categorical column.

    Args:
        df: DataFrame containing the data.
        x_col: Column name for x-axis.
        y_col: Column name for y-axis.
        strat_col: Column name for stratification.
        title: Plot title.
        output_path: Path to save the plot.
    """
    plt.figure(figsize=(12, 8))
    sns.scatterplot(data=df, x=x_col, y=y_col, hue=strat_col, palette="viridis", alpha=0.7)
    plt.title(title)
    plt.xlabel(x_col)
    plt.ylabel(y_col)
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300)
    plt.close()

    logger.log("stratified_scatter_plot_created", parameters={"path": str(output_path), "strat_col": strat_col})


@log_operation
def main() -> None:
    """
    Main entry point for plotting module.
    Generates example plots if run directly.
    """
    logger.log("plotting_start", parameters={})

    # Load data for example
    data_path = Path("data/processed/knots_cleaned.csv")
    if data_path.exists():
        df = pd.read_csv(data_path)
        # Example: Create a scatter plot
        create_scatter_plot(
            df,
            "crossing_number",
            "hyperbolic_volume",
            "Crossing Number vs Hyperbolic Volume",
            "Crossing Number",
            "Hyperbolic Volume",
            Path("data/plots/crossing_vs_volume.png")
        )
    else:
        logger.log("plotting_skipped", parameters={"reason": "Data file not found"})

    logger.log("plotting_complete", parameters={})


if __name__ == "__main__":
    main()
