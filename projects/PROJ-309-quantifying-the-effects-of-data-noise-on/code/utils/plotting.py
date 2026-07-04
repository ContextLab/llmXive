"""
Plotting utilities for the noise-effects pipeline.

Provides base plot styles and error-bar visualization helpers consistent with
the project's data-model and analysis requirements.
"""

import os
from typing import Any, Dict, List, Optional, Tuple, Union

import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np
from matplotlib.axes import Axes
from matplotlib.figure import Figure

# Ensure consistent font and style across the project
plt.style.use("seaborn-v0_8-whitegrid")
mpl.rcParams["font.family"] = "sans-serif"
mpl.rcParams["font.sans-serif"] = ["DejaVu Sans", "Arial", "Helvetica"]
mpl.rcParams["axes.edgecolor"] = "#333333"
mpl.rcParams["axes.labelcolor"] = "#333333"
mpl.rcParams["xtick.color"] = "#333333"
mpl.rcParams["ytick.color"] = "#333333"
mpl.rcParams["figure.facecolor"] = "white"
mpl.rcParams["axes.facecolor"] = "white"
mpl.rcParams["savefig.dpi"] = 300
mpl.rcParams["savefig.bbox"] = "tight"
mpl.rcParams["savefig.pad_inches"] = 0.05

# Color palette for SNR levels (low to high)
SNR_PALETTE = [
    "#d73027",  # low SNR (red)
    "#fc8d59",
    "#fee08b",
    "#e0f3f8",
    "#99d594",
    "#1b7837",  # high SNR (green)
]

# Metric-specific colors
METRIC_COLORS = {
    "Lyapunov": "#1f77b4",
    "Correlation_Dim": "#ff7f0e",
    "FNN": "#2ca02c",
}

def set_plot_style(style: str = "default") -> None:
    """
    Apply a predefined plot style.

    Args:
        style: One of 'default', 'publication', 'minimal'.
    """
    if style == "publication":
        plt.style.use("seaborn-v0_8-whitegrid")
        mpl.rcParams["font.size"] = 12
        mpl.rcParams["axes.linewidth"] = 1.2
        mpl.rcParams["lines.linewidth"] = 2.0
        mpl.rcParams["lines.markersize"] = 8
    elif style == "minimal":
        plt.style.use("seaborn-v0_8-whitegrid")
        mpl.rcParams["axes.linewidth"] = 0.5
        mpl.rcParams["lines.linewidth"] = 1.0
        mpl.rcParams["lines.markersize"] = 4
    else:
        plt.style.use("default")

def plot_error_vs_snr(
    snr_levels: List[float],
    errors: Dict[str, List[float]],
    error_std: Optional[Dict[str, List[float]]] = None,
    title: str = "Metric Error vs. SNR",
    xlabel: str = "SNR (dB)",
    ylabel: str = "Relative Error (%)",
    output_path: Optional[str] = None,
    figsize: Tuple[int, int] = (10, 6),
) -> Figure:
    """
    Plot error rates against SNR levels with optional error bars.

    Args:
        snr_levels: List of SNR values in dB.
        errors: Dict mapping metric name to list of error values.
        error_std: Optional dict of standard deviations for error bars.
        title: Plot title.
        xlabel: X-axis label.
        ylabel: Y-axis label.
        output_path: If provided, save the figure to this path.
        figsize: Figure size (width, height) in inches.

    Returns:
        The matplotlib Figure object.
    """
    fig, ax = plt.subplots(figsize=figsize)

    for i, (metric_name, err_vals) in enumerate(errors.items()):
        color = METRIC_COLORS.get(metric_name, SNR_PALETTE[i % len(SNR_PALETTE)])
        label = metric_name.replace("_", " ")

        if error_std and metric_name in error_std:
            std_vals = error_std[metric_name]
            ax.errorbar(
                snr_levels,
                err_vals,
                yerr=std_vals,
                fmt="o-",
                color=color,
                label=label,
                capsize=4,
                linewidth=2,
                markersize=6,
            )
        else:
            ax.plot(
                snr_levels,
                err_vals,
                "o-",
                color=color,
                label=label,
                linewidth=2,
                markersize=6,
            )

    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.set_xlabel(xlabel, fontsize=12)
    ax.set_ylabel(ylabel, fontsize=12)
    ax.legend(loc="best", frameon=True, fontsize=10)
    ax.grid(True, linestyle="--", alpha=0.7)
    ax.set_axisbelow(True)

    # Ensure x-axis is sorted for plotting
    ax.set_xlim(min(snr_levels), max(snr_levels))

    if output_path:
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        fig.savefig(output_path, dpi=300, bbox_inches="tight")

    return fig

def plot_threshold_marker(
    ax: Axes,
    snr_value: float,
    label: str = "Threshold",
    color: str = "red",
    linestyle: str = "--",
    linewidth: int = 2,
) -> None:
    """
    Add a vertical threshold marker to an axes object.

    Args:
        ax: The matplotlib Axes to draw on.
        snr_value: SNR value where the threshold occurs.
        label: Label for the threshold line.
        color: Line color.
        linestyle: Line style.
        linewidth: Line width.
    """
    ax.axvline(x=snr_value, color=color, linestyle=linestyle, linewidth=linewidth, label=label)
    ax.text(
        snr_value,
        ax.get_ylim()[1] * 0.95,
        label,
        color=color,
        fontsize=10,
        verticalalignment="top",
        fontweight="bold",
    )

def plot_metric_convergence(
    snr_levels: List[float],
    metric_values: List[float],
    literature_value: float,
  literature_std: Optional[float] = None,
    title: str = "Metric Convergence",
    xlabel: str = "SNR (dB)",
    ylabel: str = "Metric Value",
    output_path: Optional[str] = None,
    figsize: Tuple[int, int] = (10, 6),
) -> Figure:
    """
    Plot metric values across SNR levels with literature reference.

    Args:
        snr_levels: List of SNR values in dB.
        metric_values: List of computed metric values.
        literature_value: Reference value from literature.
        literature_std: Optional standard deviation of literature value.
        title: Plot title.
        xlabel: X-axis label.
        ylabel: Y-axis label.
        output_path: If provided, save the figure to this path.
        figsize: Figure size (width, height) in inches.

    Returns:
        The matplotlib Figure object.
    """
    fig, ax = plt.subplots(figsize=figsize)

    ax.plot(snr_levels, metric_values, "o-", color="#1f77b4", label="Computed", linewidth=2, markersize=6)

    # Plot literature value with error band if provided
    ax.axhline(y=literature_value, color="green", linestyle="--", label=f"Literature: {literature_value:.3f}")
    if literature_std:
        ax.fill_between(
            [min(snr_levels), max(snr_levels)],
            literature_value - literature_std,
            literature_value + literature_std,
            color="green",
            alpha=0.2,
            label=f"±{literature_std:.3f}",
        )

    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.set_xlabel(xlabel, fontsize=12)
    ax.set_ylabel(ylabel, fontsize=12)
    ax.legend(loc="best", frameon=True, fontsize=10)
    ax.grid(True, linestyle="--", alpha=0.7)
    ax.set_axisbelow(True)

    if output_path:
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        fig.savefig(output_path, dpi=300, bbox_inches="tight")

    return fig

def save_figure(fig: Figure, path: str, dpi: int = 300) -> None:
    """
    Save a figure to disk with standard settings.

    Args:
        fig: The matplotlib Figure to save.
        path: Output file path.
        dpi: Resolution in dots per inch.
    """
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    fig.savefig(path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)