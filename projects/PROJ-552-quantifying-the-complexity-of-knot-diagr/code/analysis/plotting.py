"""Plotting utilities for knot complexity analysis.

This module provides functions to generate figures for regression analysis,
including scatter plots of invariants, residual plots, and model fit visualizations.

All figures are saved to the ``data/plots/`` directory.
"""

from __future__ import annotations

import pathlib
from pathlib import Path
from typing import Any, Dict, List, Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure

from analysis._utils import load_cleaned_knots
from reproducibility.logs import get_logger, log_operation


def _save_figure(fig: Figure, path: Path, dpi: int = 150) -> None:
    """Helper to save a figure with proper DPI and format."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.set_size_inches(10, 8)
    fig.set_dpi(dpi)
    fig.savefig(path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    logger = get_logger(__name__)
    logger.info("Figure saved to %s", path)


@log_operation
def create_scatter_plot(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    hue_col: Optional[str] = None,
    title: str = "Scatter Plot",
    xlabel: Optional[str] = None,
    ylabel: Optional[str] = None,
    output_path: Optional[Path] = None
) -> Path:
    """
    Create a scatter plot of two variables.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing the data.
    x_col : str
        Column name for the x-axis.
    y_col : str
        Column name for the y-axis.
    hue_col : Optional[str]
        Column name for coloring points (e.g., 'alternating').
    title : str
        Plot title.
    xlabel : Optional[str]
        X-axis label.
    ylabel : Optional[str]
        Y-axis label.
    output_path : Optional[Path]
        Path to save the figure. If None, defaults to data/plots/scatter_{x}_{y}.png.

    Returns
    -------
    Path
        Path to the saved figure.
    """
    logger = get_logger(__name__)
    logger.info("Creating scatter plot: %s vs %s", x_col, y_col)

    # Drop NaN values
    plot_df = df.dropna(subset=[x_col, y_col])
    if hue_col:
        plot_df = plot_df.dropna(subset=[hue_col])

    if len(plot_df) == 0:
        raise ValueError("No data available for plotting.")

    fig, ax = plt.subplots(figsize=(10, 8))

    if hue_col:
        sns.scatterplot(
            data=plot_df,
            x=x_col,
            y=y_col,
            hue=hue_col,
            ax=ax,
            alpha=0.7,
            edgecolor=None
        )
        ax.legend(title=hue_col)
    else:
        sns.scatterplot(
            data=plot_df,
            x=x_col,
            y=y_col,
            ax=ax,
            alpha=0.7,
            edgecolor=None
        )

    ax.set_title(title)
    ax.set_xlabel(xlabel or x_col)
    ax.set_ylabel(ylabel or y_col)
    ax.grid(True, linestyle="--", alpha=0.3)

    if output_path is None:
        output_path = Path("data/plots") / f"scatter_{x_col}_vs_{y_col}.png"

    _save_figure(fig, output_path)
    return output_path


@log_operation
def create_residual_plot(
    df: pd.DataFrame,
    predictions: np.ndarray,
    residuals: np.ndarray,
    title: str = "Residual Plot",
    output_path: Optional[Path] = None
) -> Path:
    """
    Create a residual plot (residuals vs predicted values).

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing the data (used for indices).
    predictions : np.ndarray
        Array of predicted values.
    residuals : np.ndarray
        Array of residual values.
    title : str
        Plot title.
    output_path : Optional[Path]
        Path to save the figure.

    Returns
    -------
    Path
        Path to the saved figure.
    """
    logger = get_logger(__name__)
    logger.info("Creating residual plot")

    if output_path is None:
        output_path = Path("data/plots") / "residuals_vs_predictions.png"

    fig, ax = plt.subplots(figsize=(10, 8))

    # Plot residuals
    ax.scatter(predictions, residuals, alpha=0.6, edgecolor=None)

    # Plot zero line
    ax.axhline(y=0, color='r', linestyle='--', linewidth=1)

    ax.set_title(title)
    ax.set_xlabel("Predicted Values")
    ax.set_ylabel("Residuals")
    ax.grid(True, linestyle="--", alpha=0.3)

    _save_figure(fig, output_path)
    return output_path


@log_operation
def create_model_comparison_plot(
    df: pd.DataFrame,
    models: Dict[str, Any],
    x_col: str,
    y_col: str,
    output_path: Optional[Path] = None
) -> Path:
    """
    Create a plot comparing multiple model fits on the same data.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing the data.
    models : Dict[str, Any]
        Dictionary of model names to fitted model objects (must have predict method).
    x_col : str
        Column name for the x-axis.
    y_col : str
        Column name for the y-axis.
    output_path : Optional[Path]
        Path to save the figure.

    Returns
    -------
    Path
        Path to the saved figure.
    """
    logger = get_logger(__name__)
    logger.info("Creating model comparison plot")

    if output_path is None:
        output_path = Path("data/plots") / "model_comparison.png"

    # Drop NaN
    plot_df = df.dropna(subset=[x_col, y_col])
    if len(plot_df) == 0:
        raise ValueError("No data available for plotting.")

    fig, ax = plt.subplots(figsize=(10, 8))

    # Scatter actual data
    ax.scatter(plot_df[x_col], plot_df[y_col], alpha=0.5, label="Actual Data", color='gray')

    # Plot each model
    x_range = np.linspace(plot_df[x_col].min(), plot_df[x_col].max(), 100)
    for name, model in models.items():
        try:
            # Handle polynomial features if needed
            if hasattr(model, 'poly'):
                X_pred = model.poly.transform(x_range.reshape(-1, 1))
            else:
                X_pred = x_range.reshape(-1, 1)
            y_pred = model.predict(X_pred)
            ax.plot(x_range, y_pred, label=name, linewidth=2)
        except Exception as e:
            logger.warning("Could not plot model %s: %s", name, str(e))

    ax.set_title("Model Comparison")
    ax.set_xlabel(x_col)
    ax.set_ylabel(y_col)
    ax.legend()
    ax.grid(True, linestyle="--", alpha=0.3)

    _save_figure(fig, output_path)
    return output_path


@log_operation
def create_stratified_scatter_plot(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    stratify_col: str,
    title: str = "Stratified Scatter Plot",
    output_path: Optional[Path] = None
) -> Path:
    """
    Create a scatter plot stratified by a categorical variable.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing the data.
    x_col : str
        Column name for the x-axis.
    y_col : str
        Column name for the y-axis.
    stratify_col : str
        Column name for stratification (e.g., 'alternating').
    title : str
        Plot title.
    output_path : Optional[Path]
        Path to save the figure.

    Returns
    -------
    Path
        Path to the saved figure.
    """
    logger = get_logger(__name__)
    logger.info("Creating stratified scatter plot by %s", stratify_col)

    if output_path is None:
        output_path = Path("data/plots") / f"stratified_{x_col}_vs_{y_col}.png"

    # Drop NaN
    plot_df = df.dropna(subset=[x_col, y_col, stratify_col])
    if len(plot_df) == 0:
        raise ValueError("No data available for plotting.")

    fig, ax = plt.subplots(figsize=(10, 8))

    sns.scatterplot(
        data=plot_df,
        x=x_col,
        y=y_col,
        hue=stratify_col,
        style=stratify_col,
        ax=ax,
        s=100,
        alpha=0.7
    )

    ax.set_title(title)
    ax.set_xlabel(x_col)
    ax.set_ylabel(y_col)
    ax.grid(True, linestyle="--", alpha=0.3)

    _save_figure(fig, output_path)
    return output_path


@log_operation
def main() -> None:
    """
    Entry-point to generate all standard analysis plots.
    """
    logger = get_logger(__name__)
    logger.info("Starting plotting pipeline")

    df = load_cleaned_knots()

    # 1. Crossing Number vs Braid Index (stratified)
    create_stratified_scatter_plot(
        df,
        x_col="crossing_number",
        y_col="braid_index",
        stratify_col="alternating",
        title="Crossing Number vs Braid Index (Stratified by Alternating)",
        output_path=Path("data/plots/crossing_vs_braid.png")
    )

    # 2. Hyperbolic Volume vs Crossing Number
    df_hyper = df[df["hyperbolic_volume"] > 0]
    create_scatter_plot(
        df_hyper,
        x_col="crossing_number",
        y_col="hyperbolic_volume",
        hue_col="alternating",
        title="Hyperbolic Volume vs Crossing Number",
        output_path=Path("data/plots/volume_vs_crossing.png")
    )

    # 3. Hyperbolic Volume vs Braid Index
    create_scatter_plot(
        df_hyper,
        x_col="braid_index",
        y_col="hyperbolic_volume",
        hue_col="alternating",
        title="Hyperbolic Volume vs Braid Index",
        output_path=Path("data/plots/volume_vs_braid.png")
    )

    print("All plots generated in data/plots/")
