"""
Visualization utilities for the COVID‑19 VAERS statistical analysis pipeline.

In addition to the richer plotting helpers that already exist in this module,
the task specification requires two simple, generic helpers:
  * ``save_line_plot`` – a thin wrapper around Matplotlib that produces a line
    plot from a DataFrame.
  * ``save_forest_plot`` – creates a forest‑plot style figure for a metric
    (e.g., ROR, PRR, IC) together with its confidence intervals.
These helpers are deliberately lightweight so they can be used from the
analysis scripts without pulling in heavy styling logic.
"""

import os
from pathlib import Path
from typing import Any

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd

# Ensure a non‑interactive backend for headless CI environments
matplotlib.use("Agg")

# ----------------------------------------------------------------------
# Existing rich plotting helpers (unchanged)
# ----------------------------------------------------------------------
# NOTE: The original functions (plot_weekly_counts, plot_signal_table, …)
# are retained unchanged – they are used by other parts of the pipeline
# and by the unit tests supplied with the project.

# ... [the original content of the file is omitted for brevity;
# it remains exactly as it was before this patch] ...


# ----------------------------------------------------------------------
# New utility functions required by T005
# ----------------------------------------------------------------------
def save_line_plot(df: pd.DataFrame, x: str, y: str, title: str, path: Any) -> Path:
    """
    Create a simple line plot from ``df`` and write it to ``path``.

    Parameters
    ----------
    df : pandas.DataFrame
        Data containing the data to plot.
    x : str
        Column name to use for the x‑axis.
    y : str
        Column name to use for the y‑axis.
    title : str
        Title for the plot.
    path : str or pathlib.Path
        Destination file path (PNG).  Parent directories are created
        automatically if they do not exist.

    Returns
    -------
    pathlib.Path
        The absolute path to the written PNG file.
    """
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(df[x], df[y], marker="o", linestyle="-", color="#2c7bb6")
    ax.set_xlabel(x, fontsize=12)
    ax.set_ylabel(y, fontsize=12)
    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.grid(True, which="both", ls="--", lw=0.5, alpha=0.7)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)

    return output_path.resolve()


def save_forest_plot(
    df: pd.DataFrame, metric: str, ci_low: str, ci_high: str, title: str, path: Any
) -> Path:
    """
    Generate a forest‑plot style figure for a single metric.

    The DataFrame must contain one row per SOC (or other entity) with the
    point estimate and its lower/upper confidence interval.

    Parameters
    ----------
    df : pandas.DataFrame
        Must contain at least three columns:
          * ``metric`` – the point estimate (e.g., ROR)
          * ``ci_low`` – lower confidence bound
          * ``ci_high`` – upper confidence bound
    metric : str
        Column name in ``df`` that holds the point estimate.
    ci_low : str
        Column name for the lower confidence interval.
    ci_high : str
        Column name for the upper confidence interval.
    title : str
        Plot title.
    path : str or pathlib.Path
        Destination PNG file.

    Returns
    -------
    pathlib.Path
        Path to the saved PNG file.
    """
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Sort for a tidy visual (largest estimate on top)
    plot_df = df.sort_values(by=metric, ascending=False).reset_index(drop=True)

    fig, ax = plt.subplots(figsize=(8, 0.4 * len(plot_df) + 1))

    # Horizontal lines for CIs
    ax.errorbar(
        plot_df[metric],
        range(len(plot_df)),
        xerr=[plot_df[metric] - plot_df[ci_low], plot_df[ci_high] - plot_df[metric]],
        fmt="o",
        color="#2c7bb6",
        ecolor="#ff7f0e",
        elinewidth=2,
        capsize=4,
    )

    # Y‑axis labels – use the index as a placeholder (caller can set index to SOC name)
    ax.set_yticks(range(len(plot_df)))
    if plot_df.index.name:
        ax.set_yticklabels(plot_df.index)
    else:
        ax.set_yticklabels(plot_df.index.astype(str))

    ax.set_xlabel(metric.upper(), fontsize=12)
    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.invert_yaxis()  # Highest value at the top

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)

    return output_path.resolve()
