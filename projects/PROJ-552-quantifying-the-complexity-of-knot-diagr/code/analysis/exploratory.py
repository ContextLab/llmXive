"""
Exploratory analysis utilities.

Generates a stratified scatter plot of crossing number versus braid index,
separating alternating from non‑alternating knots. This module no longer
depends on the ``log_operation`` decorator (which had an incompatible
signature) and instead uses the standard ``ReproducibilityLogger`` for
simple informational logging.
"""

from __future__ import annotations

import pathlib
from pathlib import Path

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

# The logging utility provides a singleton logger via ``get_logger``.
# It does not accept any positional arguments.
from reproducibility.logs import get_logger

__all__ = [
    "load_cleaned_knots",
    "create_stratified_scatter_plot",
    "generate_exploratory_plots",
    "main",
]


def load_cleaned_knots() -> pd.DataFrame:
    """
    Load the cleaned knot dataset from ``data/processed/knots_cleaned.csv``.

    Returns
    -------
    pd.DataFrame
        The cleaned knot records.

    Raises
    ------
    FileNotFoundError
        If the expected CSV file does not exist.
    """
    data_path = Path("data/processed/knots_cleaned.csv")
    if not data_path.is_file():
        raise FileNotFoundError(
            f"Cleaned knot data not found at '{data_path}'."
        )
    return pd.read_csv(data_path)


def create_stratified_scatter_plot(df: pd.DataFrame, output_path: Path) -> None:
    """
    Generate a scatter plot of crossing number vs. braid index,
    stratified by the ``alternating`` classification.

    Parameters
    ----------
    df : pd.DataFrame
        Dataframe containing at least the columns ``crossing_number``,
        ``braid_index`` and ``alternating``.
    output_path : Path
        Destination path for the PNG figure. Parent directories are created
        automatically if they do not exist.
    """
    # Ensure the output directory exists.
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Use seaborn's relational plot for a nice faceted scatter.
    sns.set(style="whitegrid")
    g = sns.relplot(
        data=df,
        x="crossing_number",
        y="braid_index",
        hue="alternating",
        kind="scatter",
        height=6,
        aspect=1.2,
    )
    g.set_axis_labels("Crossing Number", "Braid Index")
    # Save the figure.
    g.savefig(output_path)


def generate_exploratory_plots(output_path: Path) -> None:
    """
    High‑level helper that loads the cleaned data and creates the
    stratified scatter plot.

    Parameters
    ----------
    output_path : Path
        Destination for the generated plot.
    """
    df = load_cleaned_knots()
    create_stratified_scatter_plot(df, output_path)


def main() -> None:
    """
    Entry‑point used by the project’s quick‑start script. It logs progress
    and writes the plot to ``data/plots/crossing_vs_braid.png``.
    """
    # ``get_logger`` returns the singleton ``ReproducibilityLogger``.
    logger = get_logger()
    logger.info("Running exploratory analysis: crossing number vs. braid index")
    plot_path = Path("data/plots/crossing_vs_braid.png")
    generate_exploratory_plots(plot_path)
    logger.info(f"Exploratory plot written to {plot_path}")


if __name__ == "__main__":
    main()