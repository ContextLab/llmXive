#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D

ROOT = Path(__file__).resolve().parent
DATA_PATH = ROOT / "data.json"

COL = {
    "ink": "#1B2337",
    "border": "#C9D3DE",
    "grid": "#E6EAF0",
    "neutral": "#A7B1BC",
}

HARNESS_COLORS = {
    "claudecode": "#E58B2E",
    "codex": "#5875A8",
    "deepagents": "#669B4E",
    "hermes": "#A77AA3",
    "openclaw": "#82B3AD",
}

HARNESS_LABELS = {
    "claudecode": "ClaudeCode",
    "codex": "Codex",
    "deepagents": "DeepAgents",
    "hermes": "Hermes",
    "openclaw": "OpenClaw",
}

MODEL_MARKERS = {
    "gpt-5.5": "D",
    "sonnet-4.6": "o",
    "opus-4.6": "s",
    "haiku-4.5": "^",
    "kimi-k2.6": "*",
    "MiniMax-M3": "h",
    "gpt-4.1-mini": "P",
    "qwen3-235b-a22b": "X",
    "deepseek-v4-pro": "p",
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


def nice_model(model: str) -> str:
    return MODEL_LABELS.get(model, model)


def render(data: dict) -> plt.Figure:
    df = pd.DataFrame(data["data"])
    fig, ax = plt.subplots(figsize=(12.6, 3.8))

    x = df["agent_cost_rmb"].to_numpy(dtype=float)
    y = df["score"].to_numpy(dtype=float)
    valid = x > 0
    if valid.sum() >= 3:
        coef = np.polyfit(np.log1p(x[valid]), y[valid], 1)
        xx = np.linspace(max(1.0, x[valid].min() * 0.82), x.max() * 1.04, 220)
        yy = coef[0] * np.log1p(xx) + coef[1]
        ax.plot(xx, yy, color=COL["ink"], lw=1.9, ls=(0, (5, 3)), alpha=0.48, zorder=1)

    for _, row in df.iterrows():
        harness = str(row["harness"]).lower()
        model = str(row["model"])
        color = HARNESS_COLORS.get(harness, COL["neutral"])
        marker = MODEL_MARKERS.get(model, "o")
        ax.scatter(
            row["agent_cost_rmb"],
            row["score"],
            s=260,
            marker=marker,
            c=color,
            edgecolors="white",
            linewidths=1.6,
            alpha=0.96,
            zorder=3,
        )
        ax.scatter(
            row["agent_cost_rmb"],
            row["score"],
            s=340,
            marker=marker,
            facecolors="none",
            edgecolors=mpl.colors.to_rgba(color, 0.32),
            linewidths=1.0,
            zorder=2,
        )

    ax.set_xlabel("Agent cost (RMB)", fontsize=18.8)
    ax.set_ylabel("Score", fontsize=18.8)
    ax.set_axisbelow(True)
    ax.xaxis.set_major_formatter(lambda v, pos: f"¥{v:.0f}")
    ax.set_xlim(0, df["agent_cost_rmb"].max() * 1.07)
    ax.set_ylim(0.17, 0.70)

    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
    ax.spines["left"].set_color(COL["border"])
    ax.spines["bottom"].set_color(COL["border"])
    ax.tick_params(colors=COL["ink"], labelsize=17.0, length=4.8, width=1.0)

    harness_handles = [
        Line2D([0], [0], marker="o", ls="", mfc=HARNESS_COLORS[h], mec="white", ms=14.8, label=HARNESS_LABELS[h])
        for h in ["claudecode", "codex", "deepagents", "hermes", "openclaw"]
    ]
    model_order = [
        "MiniMax-M3",
        "deepseek-v4-pro",
        "gpt-4.1-mini",
        "gpt-5.5",
        "haiku-4.5",
        "kimi-k2.6",
        "opus-4.6",
        "qwen3-235b-a22b",
        "sonnet-4.6",
    ]
    model_handles = [
        Line2D([0], [0], marker=MODEL_MARKERS[m], ls="", color=COL["ink"], ms=13.8, label=nice_model(m))
        for m in model_order
        if m in set(df["model"])
    ]

    legend1 = ax.legend(
        handles=harness_handles,
        title="Harness",
        title_fontsize=16.0,
        fontsize=14.7,
        loc="upper left",
        bbox_to_anchor=(1.015, 1.00),
        ncol=1,
        frameon=False,
        handletextpad=0.45,
        labelspacing=0.36,
        borderaxespad=0.0,
    )
    plt.setp(legend1.get_title(), color=COL["ink"])
    ax.add_artist(legend1)

    legend2 = ax.legend(
        handles=model_handles,
        title="Model",
        title_fontsize=16.0,
        fontsize=14.7,
        loc="upper left",
        bbox_to_anchor=(1.205, 1.00),
        ncol=1,
        frameon=False,
        handletextpad=0.45,
        labelspacing=0.42,
        borderaxespad=0.0,
    )
    plt.setp(legend2.get_title(), color=COL["ink"])

    fig.subplots_adjust(left=0.062, right=0.715, bottom=0.22, top=0.96)
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
