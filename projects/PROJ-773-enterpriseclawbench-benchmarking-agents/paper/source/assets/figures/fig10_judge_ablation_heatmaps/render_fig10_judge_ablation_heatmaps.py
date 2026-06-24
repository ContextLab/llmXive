#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap

ROOT = Path(__file__).resolve().parent
DATA_PATH = ROOT / "data.json"

COL = {
    "ink": "#1B2337",
    "border": "#C9D3DE",
}

HEATMAP_CMAP = LinearSegmentedColormap.from_list(
    "frontis_heatmap",
    ["#EDF4FB", "#D6E7F5", "#B9D5EB", "#8FB7D8", "#5D95C1", "#2F6C99", "#174A74"],
)


def set_style() -> None:
    mpl.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": [
                "TeX Gyre Termes",
                "Times New Roman",
                "Nimbus Roman",
                "DejaVu Serif",
                "serif",
            ],
            "axes.edgecolor": COL["border"],
            "axes.labelcolor": COL["ink"],
            "axes.titlecolor": COL["ink"],
            "xtick.color": COL["ink"],
            "ytick.color": COL["ink"],
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "savefig.facecolor": "white",
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "svg.fonttype": "none",
        }
    )


def render_panel(fig: plt.Figure, ax: plt.Axes, df: pd.DataFrame, cols: list[str], vmin: float) -> None:
    mat = df[cols].to_numpy(dtype=float)
    im = ax.imshow(mat, cmap=HEATMAP_CMAP, vmin=vmin, vmax=0.92, aspect="auto")
    ax.set_xticks(np.arange(len(cols)))
    ax.set_xticklabels(cols, rotation=35, ha="right", fontsize=13.5, color=COL["ink"])
    ax.set_yticks(np.arange(len(df)))
    ax.set_yticklabels(df["combo_label"].tolist(), fontsize=10.2, color=COL["ink"])
    ax.tick_params(length=0)

    for spine in ax.spines.values():
        spine.set_visible(False)

    ax.set_xticks(np.arange(-0.5, len(cols), 1), minor=True)
    ax.set_yticks(np.arange(-0.5, len(df), 1), minor=True)
    ax.grid(which="minor", color="white", lw=0.55)

    for i in range(mat.shape[0]):
        for j in range(mat.shape[1]):
            value = mat[i, j]
            text_color = "white" if value > 0.65 else COL["ink"]
            ax.text(j, i, f"{value:.2f}", ha="center", va="center", fontsize=8.4, color=text_color)

    cbar = fig.colorbar(im, ax=ax, orientation="vertical", fraction=0.024, pad=0.012)
    cbar.set_label("Average score", fontsize=12.8, color=COL["ink"], rotation=270, labelpad=17)
    cbar.ax.tick_params(labelsize=11.2, length=0, colors=COL["ink"])


def render(data: dict) -> plt.Figure:
    panels = data["panels"]
    text_df = pd.DataFrame(panels["text_judges"]["data"]).sort_values("rank_by_sonnet_main")
    visual_df = pd.DataFrame(panels["visual_judges"]["data"]).sort_values("rank_by_sonnet_main")
    text_cols = list(panels["text_judges"]["fields"]["judges"])
    visual_cols = list(panels["visual_judges"]["fields"]["judges"])

    fig, axes = plt.subplots(2, 1, figsize=(6.75, 13.2), gridspec_kw={"hspace": 0.34})
    render_panel(fig, axes[0], text_df, text_cols, vmin=0.18)
    render_panel(fig, axes[1], visual_df, visual_cols, vmin=0.28)
    fig.subplots_adjust(bottom=0.085, top=0.965, left=0.285, right=0.905)
    return fig


def main() -> None:
    set_style()
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    fig = render(data)
    fig.savefig(ROOT / "figure.pdf", bbox_inches="tight")
    fig.savefig(ROOT / "figure.png", dpi=220, bbox_inches="tight")
    plt.close(fig)
    print(f"Wrote {ROOT / 'figure.png'}")
    print(f"Wrote {ROOT / 'figure.pdf'}")


if __name__ == "__main__":
    main()
