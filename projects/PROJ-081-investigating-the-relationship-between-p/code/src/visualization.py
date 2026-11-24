"""
visualization.py
-----------------
Simple visualisation utilities for the analysis pipeline.
Currently provides a function to plot a correlation heat‑map with
significance annotations.
"""

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
    Generate a seaborn heatmap PNG visualising metabolite‑herbivory
    correlations. Cells display the Pearson r value; cells with
    q‑value < 0.05 are annotated with an asterisk.

    Parameters
    ----------
    corr_dict : dict
        The AnalysisResult dict returned by ``compute_correlations``.
    output_path : str
        Destination file path (including filename) for the PNG figure.
    """
    # Build a DataFrame suitable for heatmap: rows = metabolites, cols = herbivory
    metabolites = ["alkaloids", "terpenes", "phenolics", "benzoxazinoids"]
    r_vals = [corr_dict["matrix"][m] for m in metabolites]
    q_vals = [corr_dict["q_values"][m] for m in metabolites]

    heat_df = pd.DataFrame(
        data=[r_vals],
        index=["herbivory_score"],
        columns=metabolites,
    ).T

    # Prepare annotation: show r value and * if significant
    annotations = []
    for r, q in zip(r_vals, q_vals):
        ann = f"{r:.2f}"
        if q < 0.05:
            ann += "*"
        annotations.append(ann)

    plt.figure(figsize=(8, 4))
    ax = sns.heatmap(
        heat_df,
        annot=annotations,
        fmt="",
        cmap="vlag",
        center=0,
        cbar_kws={"label": "Pearson r"},
        linewidths=0.5,
        linecolor="gray",
    )
    ax.set_title("Metabolite Class vs. Herbivory Correlation")
    plt.tight_layout()

    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_path, dpi=150)
    plt.close()
    log.info(f"Correlation heatmap saved to {out_path}")