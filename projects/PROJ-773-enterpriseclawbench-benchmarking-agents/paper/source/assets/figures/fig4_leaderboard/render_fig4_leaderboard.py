#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Patch

ROOT = Path(__file__).resolve().parent
DATA_PATH = ROOT / "data.json"

COL = {
    "ink": "#1B2337",
    "border": "#C9D3DE",
    "grid": "#E6EAF0",
    "white": "#FFFFFF",
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


def money(x: float) -> str:
    return f"¥{x:.0f}"


def nice_model(model: str) -> str:
    return MODEL_LABELS.get(model, model)


def render(data: dict) -> plt.Figure:
    df = pd.DataFrame(data["data"]).sort_values("rank", ascending=True).reset_index(drop=True)
    fig, ax = plt.subplots(figsize=(12.8, 4.8))

    x = np.arange(len(df))
    colors = [HARNESS_COLORS.get(str(h).lower(), COL["neutral"]) for h in df["harness"]]
    ax.bar(x, df["score_percent"], color=colors, edgecolor=COL["white"], linewidth=0.8, width=0.82)

    # 中文注释：标题位置主要由 pad 和 y 控制；pad 增大通常会上移，y 增大也会上移。
    ax.set_title("Main leaderboard by harness-model combination", fontsize=17, weight="bold", pad=15, y=1.28)
    ax.set_ylabel("Score (%)", fontsize=12, weight="bold")
    # 中文注释：调小上限会让柱子视觉上更高；调大上限则会显得更矮。
    ax.set_ylim(0, 82)
    ax.set_xlim(-0.6, len(df) - 0.4)
    ax.set_xticks(x)
    ax.set_xticklabels([nice_model(m) for m in df["model"]], rotation=40, ha="right", fontsize=10, color=COL["ink"])
    ax.grid(axis="y", color=COL["grid"], lw=0.8, linestyle="--")
    ax.set_axisbelow(True)

    avg = df["score_percent"].mean()
    ax.axhline(avg, ls="--", color=COL["ink"], lw=1.0, alpha=0.65)
    ax.text(len(df) - 0.45, avg + 1.0, f"Avg {avg:.1f}%", fontsize=8.7, color=COL["ink"], ha="right", va="bottom")

    for xi, score in zip(x, df["score_percent"]):
        ax.text(xi, score + 1.1, f"{score:.1f}", fontsize=8.4, ha="center", va="bottom", color=COL["ink"])

    # 中文注释：顶部斜着的 cost / time 文字高度；增大上移，减小下移。
    top_y = 82.0
    for xi, cost, minutes in zip(x, df["agent_cost_rmb"], df["elapsed_avg_min"]):
        ax.text(xi, top_y, f"{money(cost)} / {minutes:.1f}m", fontsize=10, ha="center", va="bottom", rotation=38, color=COL["ink"])

    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
    ax.spines["left"].set_color(COL["ink"])
    ax.spines["bottom"].set_color(COL["ink"])
    ax.tick_params(axis="y", colors=COL["ink"], labelsize=9)
    ax.tick_params(axis="x", colors=COL["ink"])

    order = ["codex", "deepagents", "claudecode", "hermes", "openclaw"]
    handles = [Patch(fc=HARNESS_COLORS[h], label=HARNESS_LABELS[h]) for h in order if h in set(df["harness"].str.lower())]
    # 中文注释：bbox_to_anchor 的第二个值越小（越负），图例越往下。
    ax.legend(
        handles=handles,
        ncol=5,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.5),
        frameon=False,
        fontsize=10,
        handlelength=1.2,
        columnspacing=1.5,
    )
    # 中文注释：bottom 控制底部留白，top 控制顶部留白；两者需要和标题/斜字联动调整。
    fig.subplots_adjust(bottom=0.50, top=0.82)
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
