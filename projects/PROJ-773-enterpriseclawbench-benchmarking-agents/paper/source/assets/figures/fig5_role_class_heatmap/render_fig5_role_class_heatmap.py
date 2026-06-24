#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap

ROOT = Path(__file__).resolve().parent
DATA_PATH = ROOT / "data.json"

COL = {
    "ink": "#1B2337",
    "border": "#C9D3DE",
}

MODEL_LABELS = {
    "gpt-5.5": "GPT-5.5",
    "sonnet-4.6": "Sonnet 4.6",
    "opus-4.6": "Opus 4.6",
    "haiku-4.5": "Haiku 4.5",
    "kimi-k2.6": "Kimi K2.6",
    "MiniMax-M3": "MiniMax-M3",
    "gpt-4.1-mini": "GPT-4.1-mini",
    "qwen3-235b-a22b": "Qwen3-235B-A22B",
    "deepseek-v4-pro": "DeepSeek V4 Pro",
}

HEATMAP_CMAP = LinearSegmentedColormap.from_list(
    "frontis_heatmap",
    ["#EDF4FB", "#D6E7F5", "#B9D5EB", "#8FB7D8", "#5D95C1", "#2F6C99", "#174A74"],
)

HEAT_XTICK_SIZE = 14  # check: 横轴标签字号（列名大小）
HEAT_YTICK_SIZE = 14  # check: 纵轴标签字号（模型名大小）
HEAT_CELL_SIZE = 14  # check: 每个小格子中间分数字号
HEAT_CBAR_LABEL_SIZE = 14  # check: colorbar 标题字号
HEAT_CBAR_TICK_SIZE = 14  # check: colorbar 刻度字号


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


def save_figure(fig: plt.Figure) -> None:
    fig.savefig(ROOT / "figure.pdf", bbox_inches="tight", pad_inches=0.02)
    fig.savefig(ROOT / "figure.png", dpi=300, bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)


def matrix_from_records(data: dict) -> tuple[np.ndarray, list[str], list[str]]:
    records = data["data"]
    row_order = data["model_order"]
    col_order = data["column_order"]
    row_labels = []
    for row in row_order:
        match = next((r for r in records if r["model"] == row), None)
        row_labels.append(match.get("model_label", row) if match else MODEL_LABELS.get(row, row))

    col_labels: list[str] = []
    mat = []
    for row in row_order:
        vals = []
        for col in col_order:
            item = next((r for r in records if r["model"] == row and r["role_class"] == col), None)
            vals.append(np.nan if item is None else item["score"])
            if len(col_labels) < len(col_order):
                col_labels.append(col)
        mat.append(vals)
    return np.array(mat, dtype=float), row_labels, col_labels


def render(data: dict) -> plt.Figure:
    mat, row_labels, col_labels = matrix_from_records(data)
    fig, ax = plt.subplots(figsize=(6.25, 5.75))  # check: 第二个数越大，Figure 5 每个格子越高
    im = ax.imshow(mat, cmap=HEATMAP_CMAP, vmin=0.15, vmax=0.75, aspect="auto")

    ax.set_xticks(np.arange(len(col_labels)))
    ax.set_xticklabels(col_labels, rotation=30, ha="right", fontsize=HEAT_XTICK_SIZE, color=COL["ink"])
    ax.set_yticks(np.arange(len(row_labels)))
    ax.set_yticklabels(row_labels, fontsize=HEAT_YTICK_SIZE, color=COL["ink"])
    ax.tick_params(length=0)

    for spine in ax.spines.values():
        spine.set_visible(False)

    ax.set_xticks(np.arange(-0.5, mat.shape[1], 1), minor=True)
    ax.set_yticks(np.arange(-0.5, mat.shape[0], 1), minor=True)
    ax.grid(which="minor", color="white", linewidth=1.0)
    ax.tick_params(which="minor", bottom=False, left=False)

    for i in range(mat.shape[0]):
        for j in range(mat.shape[1]):
            value = mat[i, j]
            if np.isnan(value):
                continue
            text_color = "white" if value > 0.45 else COL["ink"]
            CELL_Y_OFFSET = 0.12  # check: >0 往下移，<0 往上移
            ax.text(j, i + CELL_Y_OFFSET, f"{value:.2f}", ha="center", va="center", fontsize=HEAT_CELL_SIZE, color=text_color)

    fig.subplots_adjust(bottom=0.39, top=0.985, left=0.18, right=0.985)
    cbar = fig.colorbar(im, ax=ax, orientation="horizontal", fraction=0.075, pad=0.30)
    cbar.set_label("Score", fontsize=HEAT_CBAR_LABEL_SIZE, color=COL["ink"])
    cbar.ax.tick_params(labelsize=HEAT_CBAR_TICK_SIZE, length=0, colors=COL["ink"])
    return fig


def main() -> None:
    set_style()
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    fig = render(data)
    save_figure(fig)
    print(f"Wrote {ROOT / 'figure.png'}")
    print(f"Wrote {ROOT / 'figure.pdf'}")


if __name__ == "__main__":
    main()
