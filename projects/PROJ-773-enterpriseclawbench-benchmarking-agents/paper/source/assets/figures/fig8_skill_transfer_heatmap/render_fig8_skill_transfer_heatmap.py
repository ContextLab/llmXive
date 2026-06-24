#!/usr/bin/env python3
"""Render Figure 9 as a self-contained single-column heatmap."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm


ROOT = Path(__file__).resolve().parent
DATA_PATH = ROOT / "data.json"

COL = {
    "ink": "#1B2337",
    "muted": "#697386",
    "border": "#D6DEE8",
}

GAIN_CMAP = LinearSegmentedColormap.from_list(
    "frontis_gain_delta",
    [
        (0.00, "#B85C2E"),
        (0.18, "#D99566"),
        (0.34, "#E9C9AE"),
        (0.46, "#F8F3EE"),
        (0.50, "#FFFFFF"),
        (0.54, "#F2F7FB"),
        (0.66, "#D6E7F5"),
        (0.82, "#8FB7D8"),
        (1.00, "#174A74"),
    ],
)

ROW_LABEL_SIZE = 7.8  # check: 行首标签字号（左侧 harness / consumer / avg 行名）
COL_LABEL_SIZE = 7.8  # check: 列首标签字号（顶部 model / creator 名）
CBAR_LABEL_SIZE = 7.8  # check: 图例标题字号（colorbar 标题）
CBAR_TICK_SIZE = 7.8  # check: 图例刻度字号（colorbar 数字）
CELL_TOP_TEXT_SIZE = 5.8  # check: 格子上半行 pre->post 文本字号
CELL_BOLD_TEXT_SIZE = 8.0  # check: 格子内加粗 delta 数字号


def set_style() -> None:
    mpl.rcParams.update({
        "font.family": "serif",
        "font.serif": ["TeX Gyre Termes", "Times New Roman", "Nimbus Roman", "DejaVu Serif", "serif"],
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
        "axes.titlesize": 11,  # check: matplotlib 默认标题字号（本图基本未显式用到标题）
        "axes.titleweight": "bold",
        "axes.labelsize": 9,  # check: matplotlib 默认轴标签字号
        "xtick.labelsize": 8,  # check: matplotlib 默认 x 轴刻度字号
        "ytick.labelsize": 8,  # check: matplotlib 默认 y 轴刻度字号
        "legend.fontsize": 9,  # check: matplotlib 默认 legend 字号
    })


def split_label(label: str) -> str:
    return label  # check: 保持 combo 名不换行；如果之后想恢复换行，再改回 replace("/", "/\\n")


def readable_text_color(cmap: LinearSegmentedColormap, norm: TwoSlopeNorm, value: float) -> str:
    red, green, blue, _ = cmap(norm(value))
    luminance = 0.2126 * red + 0.7152 * green + 0.0722 * blue
    return "white" if luminance < 0.58 else COL["ink"]


def render(data: dict) -> plt.Figure:
    consumers = [split_label(x) for x in data["consumers"]]
    creators = [split_label(x) for x in data["creators"]]
    baseline = np.asarray(data["baseline"], dtype=float)
    post = np.asarray(data["post"], dtype=float)
    pre = np.repeat(baseline[:, None], len(creators), axis=1)
    delta = post - pre
    heat = np.vstack([delta, np.asarray(data["mean_delta"], dtype=float)[None, :]])
    row_labels = consumers + ["Mean Delta"]

    fig, ax = plt.subplots(figsize=(3.55, 2.12), dpi=220)   # check: 第二个数越大，Figure 7 每个格子越高
    norm = TwoSlopeNorm(vmin=-0.34, vcenter=0.0, vmax=0.34)
    im = ax.imshow(heat, cmap=GAIN_CMAP, norm=norm, aspect="auto")

    ax.set_xticks(np.arange(len(creators)))
    ax.set_xticklabels(creators, rotation=0, ha="center", fontsize=COL_LABEL_SIZE, color=COL["ink"])
    ax.set_yticks(np.arange(len(row_labels)))
    ax.set_yticklabels(row_labels, fontsize=ROW_LABEL_SIZE, color=COL["ink"])
    ax.xaxis.tick_top()
    ax.tick_params(axis="x", length=0, pad=6)
    ax.tick_params(axis="y", length=0, pad=5)

    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_xticks(np.arange(-0.5, heat.shape[1], 1), minor=True)
    ax.set_yticks(np.arange(-0.5, heat.shape[0], 1), minor=True)
    ax.grid(which="minor", color="white", linewidth=1.15)
    ax.tick_params(which="minor", bottom=False, left=False)

    for i in range(heat.shape[0]):
        for j in range(heat.shape[1]):
            value = heat[i, j]
            text_color = readable_text_color(GAIN_CMAP, norm, value)
            if i < len(consumers):
                ax.text(
                    j,
                    i - 0.16,
                    f"{pre[i, j]:.3f}->{post[i, j]:.3f}",
                    ha="center",
                    va="center",
                    fontsize=CELL_TOP_TEXT_SIZE,
                    color=text_color,
                )
                ax.text(
                    j,
                    i + 0.30, # check: 格子中加粗字的高度：让它下移，就把 i + 0.17 改大一点
                    f"{value:+.3f}",
                    ha="center",
                    va="center",
                    fontsize=CELL_BOLD_TEXT_SIZE,
                    fontweight="bold",
                    color=text_color,
                )
            else:
                ax.text(
                    j,
                    i + 0.10,
                    f"{value:+.3f}",
                    ha="center",
                    va="center",
                    fontsize=CELL_BOLD_TEXT_SIZE,
                    fontweight="bold",
                    color=text_color,
                )

    cbar = fig.colorbar(im, ax=ax, orientation="horizontal", fraction=0.075, pad=0.055)
    cbar.set_label("Gain Delta", fontsize=CBAR_LABEL_SIZE, color=COL["ink"])
    cbar.set_ticks([-0.3, -0.15, 0.0, 0.15, 0.3])
    cbar.ax.tick_params(labelsize=CBAR_TICK_SIZE, length=0, colors=COL["ink"])
    cbar.outline.set_edgecolor(COL["border"])
    cbar.outline.set_linewidth(0.8)

    fig.subplots_adjust(left=0.34, right=0.985, top=0.885, bottom=0.22)
    return fig


def main() -> None:
    set_style()
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    fig = render(data)
    pdf_path = ROOT / "figure.pdf"
    png_path = ROOT / "figure.png"
    fig.savefig(pdf_path, bbox_inches="tight")
    fig.savefig(png_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"Wrote {pdf_path}")
    print(f"Wrote {png_path}")


if __name__ == "__main__":
    main()
