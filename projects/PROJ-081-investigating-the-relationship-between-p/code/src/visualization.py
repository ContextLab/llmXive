import json
from pathlib import Path
from typing import Dict

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

from llmxive_toolkit import get_logger

log = get_logger(__name__)


def plot_correlation_heatmap(corr_dict: Dict, output_path: str) -> None:
    """
    Generate a seaborn heatmap PNG visualising metabolite‑herbivory correlations.

    Parameters
    ----------
    corr_dict : dict
        The AnalysisResult dict returned by ``compute_correlations``.
    output_path : str
        Destination file path (including filename) for the PNG figure.
    """
    # Build a DataFrame suitable for heatmap: metabolites as rows, herbivory_score as column
    matrix = corr_dict.get("matrix", {})
    q_vals = corr_dict.get("q_values", {})

    if not matrix:
        raise ValueError("Correlation matrix is empty; cannot plot heatmap.")

    df_plot = pd.Series(matrix, name="herbivory_score").to_frame()

    # Create annotation strings with asterisk for significance
    annot = pd.Series(
        {
            met: f"{matrix[met]:.2f}{'*' if q_vals.get(met, 1) < 0.05 else ''}"
            for met in matrix
        },
        name="herbivory_score",
    ).to_frame()

    # Plot
    plt.figure(figsize=(4, 4))
    sns.set(style="whitegrid")
    ax = sns.heatmap(
        df_plot,
        annot=annot,
        fmt="",
        cmap="vlag",
        center=0,
        cbar_kws={"label": "Pearson r"},
        linewidths=0.5,
        linecolor="gray",
    )
    ax.set_ylabel("")
    ax.set_xlabel("")
    ax.set_yticklabels(df_plot.index, rotation=0)
    ax.set_xticklabels(["herbivory_score"], rotation=0)

    # Ensure the output directory exists
    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(out_path, dpi=300)
    plt.close()
    log.info(f"Correlation heatmap saved to {out_path}")
