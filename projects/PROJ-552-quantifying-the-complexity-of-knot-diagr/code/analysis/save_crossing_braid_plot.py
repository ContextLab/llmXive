"""Generate and save a scatter plot of crossing number vs. braid index.

This script loads the cleaned knot dataset, creates a scatter plot showing the
relationship between crossing number and braid index, and saves the figure to
``data/plots/crossing_vs_braid.png`` with a resolution of 1200×900 pixels.

The script is intended to be executed directly:

    python code/analysis/save_crossing_braid_plot.py

It uses the project's reproducibility logging utilities to record the operation.
"""

from __future__ import annotations

import pathlib
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

# The project’s logging utilities expose a parameter‑less ``get_logger``.
from reproducibility.logs import get_logger

# Helper to load the processed dataset.
from analysis.data_quantities import load_cleaned_knots_data


def create_crossing_vs_braid_plot(
    df: pd.DataFrame,
    output_path: Path,
    *,
    fig_width: float = 12,
    fig_height: float = 9,
    dpi: int = 100,
) -> None:
    """
    Create a scatter plot of crossing number vs. braid index.

    Parameters
    ----------
    df: pd.DataFrame
        DataFrame containing at least the columns ``crossing_number`` and
        ``braid_index``. An optional ``alternating`` column is used for colour
        coding; if absent, all points are plotted in a single colour.
    output_path: Path
        Destination file for the PNG image.
    fig_width, fig_height: float
        Figure size in inches (defaults give 1200×900 @ 100 dpi).
    dpi: int
        Dots per inch for the saved PNG.
    """
    logger = get_logger()
    logger.info("Generating crossing‑vs‑braid plot")

    # Ensure required columns exist; raise a clear error otherwise.
    required = {"crossing_number", "braid_index"}
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"Missing required columns for plot: {missing}")

    # Use alternating classification for colour if present.
    if "alternating" in df.columns:
        categories = df["alternating"].astype(str)
        palette = {"True": "#1f77b4", "False": "#ff7f0e"}
        colors = categories.map(palette).fillna("#7f7f7f")
        label = "Alternating"  # legend handled manually below
    else:
        colors = "#1f77b4"
        label = None

    plt.figure(figsize=(fig_width, fig_height), dpi=dpi)
    scatter = plt.scatter(
        df["crossing_number"],
        df["braid_index"],
        c=colors,
        alpha=0.7,
        edgecolors="w",
        linewidths=0.5,
    )

    plt.title("Crossing Number vs. Braid Index")
    plt.xlabel("Crossing Number")
    plt.ylabel("Braid Index")

    if label:
        # Create a simple legend for alternating vs non‑alternating.
        from matplotlib.lines import Line2D

        legend_elements = [
            Line2D([0], [0], marker="o", color="w", label="Alternating",
                   markerfacecolor=palette["True"], markersize=8),
            Line2D([0], [0], marker="o", color="w", label="Non‑alternating",
                   markerfacecolor=palette["False"], markersize=8),
        ]
        plt.legend(handles=legend_elements, title="Classification")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(output_path, dpi=dpi)
    plt.close()
    logger.info(f"Plot saved to {output_path}")


def main() -> None:
    """Entry point for the script."""
    logger = get_logger()
    logger.info("Starting crossing‑vs‑braid plot generation")

    # Load the cleaned dataset (CSV created by earlier pipeline steps).
    df = load_cleaned_knots_data()

    # Destination path as specified by the task.
    output_file = Path("data/plots/crossing_vs_braid.png")

    create_crossing_vs_braid_plot(df, output_file)
    logger.info("Crossing vs. braid plot generation completed")


if __name__ == "__main__":
    main()