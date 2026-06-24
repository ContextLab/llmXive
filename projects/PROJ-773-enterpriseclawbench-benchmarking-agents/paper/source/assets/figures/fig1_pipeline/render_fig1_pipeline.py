#!/usr/bin/env python3
"""
Redraw EnterpriseClawBench / FrontisBench manuscript figures from data.zip
using a unified academic visual system.

Directly drawable figures from data.zip:
  fig:pipeline                  -> fig1_pipeline
  fig:funnel                    -> fig2_funnel
  fig:leaderboard               -> fig4_leaderboard
  fig:score-cost                -> fig9_score_cost
  fig:benchmark-stats-main      -> fig3_benchmark_statistics
  fig:role-class-main           -> fig5_role_class_heatmap
  fig:artifact-main             -> fig6_artifact_type_heatmap
  fig:radar-main                -> fig7_dimension_profile_heatmap
  fig:judge-appendix            -> fig10_judge_ablation_heatmaps

Run:
  python frontis_unified_figures.py --zip data.zip --out figures_unified
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from zipfile import ZipFile

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import patches
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

# -----------------------------
# 1. Unified visual standard
# -----------------------------
COL = {
    "ink": "#1B2337",
    "slate": "#51657D",
    "border": "#C9D3DE",
    "grid": "#E6EAF0",
    "light": "#EFF3F7",
    "neutral": "#A7B1BC",
    "primary_blue": "#5B7DBE",
    "secondary_blue": "#89A9D8",
    "teal": "#2E9C9A",
    "deep_teal": "#1F6F78",
    "green": "#5F9D68",
    "purple": "#7C6ACF",
    "orange": "#E58B2E",
    "red": "#D45452",
    "white": "#FFFFFF",
}

HARNESS_COLORS = {
    "claudecode": "#D9831F",
    "codex": "#2E9C9A",
    "deepagents": "#2A7F62",
    "hermes": "#7C6ACF",
    "openclaw": "#4E7FD1",
}
HARNESS_LABELS = {
    "claudecode": "ClaudeCode",
    "codex": "Codex",
    "deepagents": "DeepAgents",
    "hermes": "Hermes",
    "openclaw": "OpenClaw",
}

ROLE_COLORS = {
    "Product / project": "#5875A8",
    "Engineering / IT": "#D45452",
    "HR / admin": "#669B4E",
    "Executive": "#A77AA3",
    "Sales / customer": "#E58B2E",
    "Marketing": "#82B3AD",
    "Finance / ops": "#425C78",
    "Others": "#A7B1BA",
}

FILE_COLORS = {
    "MD": "#5875A8",
    "TXT": "#D45452",
    "DOC/DOCX": "#82B3AD",
    "Image": "#669B4E",
    "PDF": "#E58B2E",
    "Sheet": "#A77AA3",
    "Code": "#425C78",
    "HTML": "#2E9C9A",
    "Other": "#A7B1BA",
    "Other files": "#A7B1BA",
    "Slides": "#8FB7D8",
    "Archive/package": "#51657D",
    "Skill/package": "#7C6ACF",
    "JSON": "#B9C2CC",
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

HEATMAP_COLORS = ["#EDF4FB", "#D6E7F5", "#B9D5EB", "#8FB7D8", "#5D95C1", "#2F6C99", "#174A74"]
HEATMAP_CMAP = LinearSegmentedColormap.from_list("frontis_heatmap", HEATMAP_COLORS)


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
        "axes.titlesize": 11,
        "axes.titleweight": "bold",
        "axes.labelsize": 9,
        "xtick.labelsize": 8,
        "ytick.labelsize": 8,
        "legend.fontsize": 9,
    })


def load_jsons(zip_path: str | Path) -> dict[str, dict]:
    out = {}
    with ZipFile(zip_path) as zf:
        for name in zf.namelist():
            if name.startswith("data/") and name.endswith(".json"):
                with zf.open(name) as f:
                    out[Path(name).name] = json.load(f)
    return out


def save_figure(fig: plt.Figure, out_dir: Path, stem: str, png: bool = True, pdf: bool = True, svg: bool = False) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    if pdf:
        fig.savefig(out_dir / f"{stem}.pdf", bbox_inches="tight", pad_inches=0.02)
    if svg:
        fig.savefig(out_dir / f"{stem}.svg", bbox_inches="tight", pad_inches=0.02)
    if png:
        fig.savefig(out_dir / f"{stem}.png", dpi=300, bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)


def money(x: float) -> str:
    return f"¥{x:.0f}"


def fmt_count(x: int | float) -> str:
    return f"{int(round(x)):,}"


def lighten(hex_color: str, alpha: float = 0.12) -> tuple[float, float, float, float]:
    # return RGBA with low alpha over white
    rgb = mpl.colors.to_rgb(hex_color)
    return (*rgb, alpha)


def nice_harness(h: str) -> str:
    return HARNESS_LABELS.get(str(h).lower(), str(h))


def nice_model(m: str) -> str:
    return MODEL_LABELS.get(str(m), str(m))


# -----------------------------
# 2. Figure 1: Pipeline
# -----------------------------
def draw_pipeline(data: dict) -> plt.Figure:
    stages = data["data"]["stages"]
    fig, ax = plt.subplots(figsize=(15.5, 4.9))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    ax.text(0.02, 0.94, "EnterpriseClawBench Pipeline", fontsize=20, weight="bold", color=COL["ink"], ha="left", va="top")
    ax.text(0.02, 0.885, "Real enterprise sessions are converted into reproducible, artifact-centric benchmark tasks.", fontsize=10.5, color=COL["ink"], ha="left")

    x0s = [0.025, 0.205, 0.49, 0.67, 0.835]
    widths = [0.155, 0.26, 0.155, 0.14, 0.145]
    header_cols = ["#5B7DBE", "#89A9D8", "#5D95C1", "#2E9C9A", "#1F6F78"]
    fills = [lighten(c, 0.08) for c in header_cols]
    y0, h = 0.17, 0.63

    bullets = [
        ["Feishu / enterprise workspace", "persistent Linux sandbox", "uploaded files, chat traces,\ntool traces, generated artifacts"],
        ["split / merge sessions", "parallel mechanical checks", "reproducibility gate"],
        ["self-contained filtering", "single-turn task rewriting", "role / skill taxonomy", "expected deliverables"],
        ["input fixtures", "hard rules", "semantic rubrics", "text / visual judge routes"],
        ["non-stateful sandbox runs", "harness–model combinations", "artifact collection", "rule + semantic judging"],
    ]

    for i, (s, x, w, c, fill) in enumerate(zip(stages, x0s, widths, header_cols, fills)):
        box = patches.FancyBboxPatch((x, y0), w, h, boxstyle="round,pad=0.006,rounding_size=0.015",
                                     linewidth=0.9, edgecolor=mpl.colors.to_rgba(c, 0.55), facecolor=fill)
        ax.add_patch(box)
        ax.add_patch(patches.FancyBboxPatch((x, y0+h-0.095), w, 0.095,
                                            boxstyle="round,pad=0.006,rounding_size=0.015",
                                            linewidth=0, facecolor=c))
        ax.add_patch(patches.Rectangle((x, y0+h-0.095), w, 0.04, linewidth=0, facecolor=c))
        title = f"{i+1}. {s['stage']}"
        if i == 1:
            title = "2. Task Recovery and\nParallel Mechanical Checks"
        ax.text(x+0.012, y0+h-0.049, title, fontsize=8.8 if i != 1 else 8.2, weight="bold", color="white", ha="left", va="center")
        # bullets
        by = y0+h-0.15
        for j,b in enumerate(bullets[i]):
            ax.text(x+0.017, by-j*0.066, "•", fontsize=10, color=c, va="top")
            ax.text(x+0.032, by-j*0.066, b, fontsize=7.7, color=COL["ink"], va="top", linespacing=1.25)
        # count badge
        bw = w*0.82
        bx = x + (w-bw)/2
        bh = 0.105
        badge_col = COL["green"] if i > 1 else c
        if i == 4:
            badge_text = "120\nLite subset"
        else:
            badge_text = f"{fmt_count(s['count'])}\n{s['unit']}"
        ax.add_patch(patches.FancyBboxPatch((bx, y0+0.035), bw, bh, boxstyle="round,pad=0.004,rounding_size=0.01",
                                            linewidth=0.9, edgecolor=badge_col, facecolor="white"))
        ax.text(x+w/2, y0+0.09, badge_text, fontsize=10.5 if i!=4 else 9.2, weight="bold", color=badge_col, ha="center", va="center", linespacing=1.25)
        # arrows between boxes
        if i < 4:
            ax.annotate("", xy=(x0s[i+1]-0.008, y0+0.34), xytext=(x+w+0.008, y0+0.34),
                        arrowprops=dict(arrowstyle="-|>", lw=1.4, color=COL["primary_blue"], shrinkA=0, shrinkB=0))

    # specific gate note in stage 2
    gx, gy = x0s[1]+0.09, y0+0.18
    ax.add_patch(patches.FancyBboxPatch((gx, gy), 0.11, 0.07, boxstyle="round,pad=0.004,rounding_size=0.01",
                                        linewidth=1.0, edgecolor=COL["orange"], facecolor=lighten(COL["orange"], 0.08), linestyle="--"))
    ax.text(gx+0.055, gy+0.035, "Reproducibility\ngate", ha="center", va="center", fontsize=7.5, color=COL["orange"], weight="bold")

    # legend
    legend_items = [(COL["primary_blue"], "Data flow"), (COL["green"], "Validated artifacts / successful outputs"), (COL["orange"], "Filters / gates")]
    lx = 0.035
    for col, lab in legend_items:
        if lab == "Data flow":
            ax.annotate("", xy=(lx+0.035, 0.09), xytext=(lx, 0.09), arrowprops=dict(arrowstyle="-|>", lw=1.4, color=col))
            ax.text(lx+0.045, 0.09, lab, fontsize=8.2, va="center")
            lx += 0.14
        else:
            ax.add_patch(patches.FancyBboxPatch((lx, 0.078), 0.018, 0.024, boxstyle="round,pad=0.002,rounding_size=0.004", ec=col, fc="white", lw=1.0))
            ax.text(lx+0.026, 0.09, lab, fontsize=8.2, va="center")
            lx += 0.25
    return fig


# -----------------------------
# 3. Figure 2: Funnel
# -----------------------------
def draw_funnel(data: dict) -> plt.Figure:
    stages = data["data"]["stages"]
    by_name = {s["stage"]: s for s in stages}
    fig, ax = plt.subplots(figsize=(5.7, 9.2))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    ax.plot([0.06, 0.94], [0.965, 0.965], lw=1.8, color=COL["ink"], solid_capstyle="round")
    ax.text(0.06, 0.93, "Construction Funnel", fontsize=21, weight="bold", color=COL["ink"], ha="left", va="top")
    ax.text(0.06, 0.89, "Parallel mechanical checks converge into serial benchmark packaging.", fontsize=9.8, color=COL["ink"], ha="left")

    # Raw bar
    ax.add_patch(patches.FancyBboxPatch((0.07, 0.82), 0.86, 0.07, boxstyle="round,pad=0.01,rounding_size=0.018", fc=COL["ink"], ec="none"))
    ax.text(0.10, 0.855, "Raw MetaAgent TaskInstances", fontsize=11.5, weight="bold", color="white", va="center")
    ax.text(0.88, 0.855, fmt_count(by_name["Raw MetaAgent TaskInstances"]["count"]), fontsize=19, weight="bold", color="white", ha="right", va="center")
    ax.annotate("", xy=(0.5, 0.785), xytext=(0.5, 0.82), arrowprops=dict(arrowstyle="-|>", lw=1.2, color=COL["ink"]))
    ax.text(0.5, 0.765, "Three parallel early checks", fontsize=10.5, weight="bold", ha="center", color=COL["ink"])

    card_y, card_h, card_w = 0.64, 0.095, 0.27
    cards = [
        (0.08, "Length\nfilter", by_name["Length filter"], COL["primary_blue"]),
        (0.365, "Fixture\nlookup", by_name["Fixture lookup"], COL["red"]),
        (0.65, "Redaction\nrecovery", by_name["Redaction recovery"], COL["green"]),
    ]
    for x, title, s, col in cards:
        ax.add_patch(patches.FancyBboxPatch((x, card_y), card_w, card_h, boxstyle="round,pad=0.01,rounding_size=0.015", fc=lighten(col, 0.08), ec=col, lw=0.8))
        ax.text(x+card_w/2, card_y+0.068, title, fontsize=8.7, weight="bold", color=COL["ink"], ha="center", va="center")
        ax.text(x+card_w/2, card_y+0.038, fmt_count(s["count"]), fontsize=14, weight="bold", color=col, ha="center", va="center")
        ax.text(x+card_w/2, card_y+0.013, s.get("status", ""), fontsize=8.4, color=COL["ink"], ha="center", va="center")
    # arrows into gate
    ax.annotate("", xy=(0.42, 0.56), xytext=(0.21, card_y), arrowprops=dict(arrowstyle="-|>", lw=1.1, color=COL["ink"], connectionstyle="arc3,rad=.25"))
    ax.annotate("", xy=(0.50, 0.56), xytext=(0.50, card_y), arrowprops=dict(arrowstyle="-|>", lw=1.1, color=COL["ink"]))
    ax.annotate("", xy=(0.58, 0.56), xytext=(0.78, card_y), arrowprops=dict(arrowstyle="-|>", lw=1.1, color=COL["ink"], connectionstyle="arc3,rad=-.25"))

    def trap(y, h, top_w, bot_w, color, lines):
        cx = 0.5
        pts = [(cx-top_w/2, y+h), (cx+top_w/2, y+h), (cx+bot_w/2, y), (cx-bot_w/2, y)]
        ax.add_patch(patches.Polygon(pts, closed=True, fc=color, ec="white", lw=1.0))
        ax.text(cx, y+h*0.64, lines[0], fontsize=10.5, weight="bold", color="white", ha="center", va="center")
        ax.text(cx, y+h*0.39, lines[1], fontsize=16.5, weight="bold", color="white", ha="center", va="center")
        if len(lines) > 2:
            ax.text(cx, y+h*0.18, lines[2], fontsize=8.6, color="white", ha="center", va="center")

    trap(0.47, 0.075, 0.82, 0.70, COL["deep_teal"], ["Public-Network Gate", f"{fmt_count(by_name['Public-Network Gate']['count'])} passed", "packaged workspace or stable public access"])
    ax.annotate("", xy=(0.5, 0.44), xytext=(0.5, 0.47), arrowprops=dict(arrowstyle="-|>", lw=1.2, color=COL["ink"]))
    trap(0.35, 0.075, 0.70, 0.58, COL["primary_blue"], ["Mechanical Join", f"{fmt_count(by_name['Mechanical Join']['count'])} usable", "length + fixture + redaction + network"])
    ax.annotate("", xy=(0.5, 0.32), xytext=(0.5, 0.35), arrowprops=dict(arrowstyle="-|>", lw=1.2, color=COL["ink"]))
    trap(0.24, 0.07, 0.58, 0.46, COL["purple"], ["Self-Contained Review", f"{fmt_count(by_name['Self-Contained Review']['count'])} kept", "single-turn rewrite candidates"])
    ax.annotate("", xy=(0.5, 0.21), xytext=(0.5, 0.24), arrowprops=dict(arrowstyle="-|>", lw=1.2, color=COL["ink"]))
    trap(0.13, 0.07, 0.46, 0.34, COL["teal"], ["Package + Preflight", f"{fmt_count(by_name['Package + Preflight']['count'])} tasks", "taxonomy, rules, rubrics and judge routes"])
    ax.annotate("", xy=(0.5, 0.10), xytext=(0.5, 0.13), arrowprops=dict(arrowstyle="-|>", lw=1.2, color=COL["ink"]))
    ax.add_patch(patches.FancyBboxPatch((0.19, 0.06), 0.62, 0.035, boxstyle="round,pad=0.01,rounding_size=0.02", fc=COL["light"], ec=COL["border"], lw=0.8))
    ax.text(0.5, 0.078, "Final pool for hard120 sampling and full-pool evaluation", fontsize=8.5, weight="bold", ha="center", va="center", color=COL["ink"])
    return fig


# -----------------------------
# 4. Figure 3: Leaderboard
# -----------------------------
def draw_leaderboard(data: dict) -> plt.Figure:
    df = pd.DataFrame(data["data"]).sort_values("rank", ascending=True).reset_index(drop=True)
    fig, ax = plt.subplots(figsize=(12.8, 4.8))
    x = np.arange(len(df))
    colors = [HARNESS_COLORS.get(str(h).lower(), COL["neutral"]) for h in df["harness"]]
    ax.bar(x, df["score_percent"], color=colors, edgecolor=COL["white"], linewidth=0.8, width=0.82)

    ax.set_title("Main Lite leaderboard by harness-model combination", fontsize=17, weight="bold", pad=14)
    ax.set_ylabel("Score (%)", fontsize=12, weight="bold")
    ax.set_ylim(0, 92)
    ax.set_xlim(-0.6, len(df)-0.4)
    ax.set_xticks(x)
    ax.set_xticklabels(df["combo"].tolist(), rotation=40, ha="right", fontsize=8.3, color=COL["ink"])
    ax.grid(axis="y", color=COL["grid"], lw=0.8, linestyle="--")
    ax.set_axisbelow(True)

    avg = df["score_percent"].mean()
    ax.axhline(avg, ls="--", color=COL["ink"], lw=1.0, alpha=0.65)
    ax.text(len(df)-0.45, avg+1.0, f"Avg {avg:.1f}%", fontsize=8.7, color=COL["ink"], ha="right", va="bottom")

    for xi, sc in zip(x, df["score_percent"]):
        ax.text(xi, sc + 1.1, f"{sc:.1f}", fontsize=8.4, ha="center", va="bottom", color=COL["ink"])

    top_y = 81.0
    for xi, cost, tmin in zip(x, df["agent_cost_rmb"], df["elapsed_avg_min"]):
        ax.text(xi, top_y, f"{money(cost)} / {tmin:.1f}m", fontsize=7.2, ha="center", va="bottom", rotation=38, color=COL["ink"])

    for sp in ["top", "right"]:
        ax.spines[sp].set_visible(False)
    ax.spines["left"].set_color(COL["ink"])
    ax.spines["bottom"].set_color(COL["ink"])
    ax.tick_params(axis="y", colors=COL["ink"], labelsize=9)
    ax.tick_params(axis="x", colors=COL["ink"])

    order = ["codex", "deepagents", "claudecode", "hermes", "openclaw"]
    handles = [Patch(fc=HARNESS_COLORS[h], label=HARNESS_LABELS[h]) for h in order if h in set(df["harness"].str.lower())]
    ax.legend(handles=handles, ncol=5, loc="upper center", bbox_to_anchor=(0.5, -0.58),
              frameon=False, fontsize=9.2, handlelength=1.2, columnspacing=1.5)
    fig.subplots_adjust(bottom=0.58, top=0.86)
    return fig


# -----------------------------
# 5. Figure 4: Score-cost scatter
# -----------------------------
def draw_score_cost(data: dict) -> plt.Figure:
    df = pd.DataFrame(data["data"])
    fig, ax = plt.subplots(figsize=(7.4, 5.2))
    for _, r in df.iterrows():
        h = str(r["harness"]).lower()
        m = str(r["model"])
        ax.scatter(r["agent_cost_rmb"], r["score"], s=78, marker=MODEL_MARKERS.get(m, "o"),
                   c=HARNESS_COLORS.get(h, COL["neutral"]), edgecolors="white", linewidths=0.9, alpha=0.95, zorder=3)
    ax.set_title("Score vs. agent cost by harness-model combination", loc="left", pad=8, fontsize=12.5)
    ax.set_xlabel("Agent cost (RMB)", fontsize=10.5)
    ax.set_ylabel("Score", fontsize=10.5)
    ax.grid(color=COL["grid"], lw=0.8)
    ax.set_axisbelow(True)
    ax.xaxis.set_major_formatter(lambda x, pos: f"¥{x:.0f}")
    ax.set_xlim(0, df["agent_cost_rmb"].max()*1.08)
    ax.set_ylim(max(0, df["score"].min()-0.04), df["score"].max()+0.04)
    for sp in ["top", "right"]:
        ax.spines[sp].set_visible(False)
    ax.tick_params(colors=COL["ink"], labelsize=9)
    h_handles = [Line2D([0],[0], marker="o", ls="", mfc=HARNESS_COLORS[h], mec="white", ms=8, label=HARNESS_LABELS[h]) for h in ["claudecode","codex","deepagents","hermes","openclaw"]]
    m_order = ["MiniMax-M3", "deepseek-v4-pro", "gpt-4.1-mini", "gpt-5.5", "haiku-4.5", "kimi-k2.6", "opus-4.6", "qwen3-235b-a22b", "sonnet-4.6"]
    m_handles = [Line2D([0],[0], marker=MODEL_MARKERS[m], ls="", color=COL["ink"], ms=7, label=nice_model(m)) for m in m_order if m in set(df["model"])]
    leg1 = ax.legend(handles=h_handles, title="Harness", title_fontsize=10.5, fontsize=9.6, loc="upper left", bbox_to_anchor=(0.0, -0.18), ncol=5, frameon=False, handletextpad=0.5, columnspacing=1.0)
    plt.setp(leg1.get_title(), color=COL["ink"])
    ax.add_artist(leg1)
    leg2 = ax.legend(handles=m_handles, title="Model", title_fontsize=10.5, fontsize=9.4, loc="upper left", bbox_to_anchor=(0.0, -0.34), ncol=5, frameon=False, handletextpad=0.5, columnspacing=1.0)
    plt.setp(leg2.get_title(), color=COL["ink"])
    fig.subplots_adjust(bottom=0.36)
    return fig


# -----------------------------
# 6. Figure 5: Benchmark statistics
# -----------------------------
def pie_legend_labels(data, label_key, value_key):
    total = sum(d[value_key] for d in data)
    return [f"{d[label_key]}  {d[value_key]} ({d[value_key]/total:.0%})" for d in data]


def draw_donut(ax, data, label_key, value_key, colors, center_top, center_bottom, title):
    vals = [d[value_key] for d in data]
    labs = [d[label_key] for d in data]
    cols = [colors.get(l, COL["neutral"]) for l in labs]
    wedges, _ = ax.pie(vals, startangle=90, counterclock=False, colors=cols, wedgeprops=dict(width=0.42, edgecolor="white", linewidth=1.0))
    ax.text(0, 0.05, center_top, ha="center", va="center", fontsize=15, weight="bold", color=COL["ink"])
    ax.text(0, -0.13, center_bottom, ha="center", va="center", fontsize=9.2, color=COL["ink"])
    ax.set_title(title, loc="left", fontsize=11, pad=4)
    ax.axis("equal")
    ax.axis("off")
    return wedges, labs


def draw_benchmark_stats(data: dict) -> plt.Figure:
    panels = data["panels"]
    fig = plt.figure(figsize=(13.2, 7.4))
    gs = fig.add_gridspec(2, 2, width_ratios=[1.05, 1.32], height_ratios=[1,1], wspace=0.22, hspace=0.28)

    # A role pie + legend
    sg = gs[0,0].subgridspec(1,2, width_ratios=[1.0,1.12], wspace=0.02)
    ax = fig.add_subplot(sg[0,0]); axl = fig.add_subplot(sg[0,1]); axl.axis("off")
    role_data = panels["A_role_classes"]["data"]
    draw_donut(ax, role_data, "role_class", "task_count", ROLE_COLORS, "852", "tasks", "A. Role classes")
    total = sum(d["task_count"] for d in role_data)
    y=0.90
    for d in role_data:
        lab=d["role_class"]; val=d["task_count"]
        axl.add_patch(patches.Rectangle((0.02,y-0.025),0.035,0.035,fc=ROLE_COLORS[lab],ec="white",lw=0.5))
        axl.text(0.07,y-0.007,f"{lab}  {val} ({val/total:.0%})",fontsize=10.8,va="center", color=COL["ink"])
        y-=0.092

    # B skill subclass panel
    axb = fig.add_subplot(gs[0,1]); axb.axis("off"); axb.set_xlim(0,1); axb.set_ylim(0,1)
    axb.set_title("B. Skill subclasses within roles", loc="left", fontsize=12.5, pad=4)
    axb.text(0.46,0.91,"subclasses",fontsize=10.2,weight="bold", color=COL["ink"])
    axb.text(0.76,0.91,"inst. / subclass",fontsize=10.2,weight="bold", color=COL["ink"])
    bdata = panels["B_skill_subclasses"]["data"]
    y0=0.82; dy=0.105
    for i,d in enumerate(bdata):
        y=y0-i*dy; role=d["role_class"]; col=ROLE_COLORS.get(role,COL["neutral"])
        if i>0: axb.plot([0,0.985],[y+0.05,y+0.05],color=COL["grid"],lw=0.8)
        axb.text(0.00,y,role,fontsize=10.2,va="center", color=COL["ink"])
        axb.add_patch(patches.Rectangle((0.46,y-0.017),0.16,0.034,fc=col,ec=col,alpha=0.9))
        axb.text(0.64,y,str(d["subclass_count"]),fontsize=11.0,weight="bold",va="center", color=COL["ink"])
        vals=d["instance_counts_by_subclass_json"]; xs=np.linspace(0.80,0.965,len(vals))
        vmax=max(v for row in bdata for v in row["instance_counts_by_subclass_json"])
        for x,v in zip(xs,vals):
            axb.scatter(x,y,s=18+70*(v/vmax),color=col,edgecolor="white",lw=0.5,zorder=3)
            if v>=26:
                axb.text(x,y+0.035,str(v),fontsize=7.7,ha="center",color=COL["ink"])

    # C input fixtures with two-column legend
    sg = gs[1,0].subgridspec(1,2, width_ratios=[1.0,1.30], wspace=0.03)
    ax = fig.add_subplot(sg[0,0]); axl = fig.add_subplot(sg[0,1]); axl.axis("off")
    cdata = panels["C_input_fixture_files"]["display_data"]
    fcols = {d["fixture_type"]: FILE_COLORS.get(d["fixture_type"], COL["neutral"]) for d in cdata}
    total = sum(d["file_count"] for d in cdata)
    draw_donut(ax, cdata, "fixture_type", "file_count", fcols, fmt_count(total), "files", "C. Input fixture files")
    ncols = 2
    rows = int(math.ceil(len(cdata)/ncols))
    y_start = 0.93
    dy = 0.118
    x_positions = [0.02, 0.52]
    for idx, d in enumerate(cdata):
        col_idx = idx // rows
        row_idx = idx % rows
        x0 = x_positions[col_idx]
        y = y_start - row_idx*dy
        lab=d["fixture_type"]; val=d["file_count"]
        axl.add_patch(patches.Rectangle((x0,y-0.022),0.028,0.028,fc=fcols[lab],ec="white",lw=0.4))
        axl.text(x0+0.04,y-0.006,f"{lab}  {val} ({val/total:.0%})",fontsize=10.2,va="center", color=COL["ink"])
    axl.set_xlim(0,1); axl.set_ylim(0,1)

    # D deliverables with two-column legend
    sg = gs[1,1].subgridspec(1,2, width_ratios=[1.0,1.34], wspace=0.04)
    ax = fig.add_subplot(sg[0,0]); axl = fig.add_subplot(sg[0,1]); axl.axis("off")
    ddata = panels["D_expected_deliverables"]["display_data"]
    dcols = {d["deliverable_type"]: FILE_COLORS.get(d["deliverable_type"], COL["neutral"]) for d in ddata}
    total = sum(d["requirement_count"] for d in ddata)
    draw_donut(ax, ddata, "deliverable_type", "requirement_count", dcols, fmt_count(total), "requirements", "D. Expected deliverables")
    ncols = 2
    rows = int(math.ceil(len(ddata)/ncols))
    y_start = 0.93
    dy = 0.118
    x_positions = [0.02, 0.54]
    for idx, d in enumerate(ddata):
        col_idx = idx // rows
        row_idx = idx % rows
        x0 = x_positions[col_idx]
        y = y_start - row_idx*dy
        lab=d["deliverable_type"]; val=d["requirement_count"]
        axl.add_patch(patches.Rectangle((x0,y-0.022),0.028,0.028,fc=dcols[lab],ec="white",lw=0.4))
        axl.text(x0+0.04,y-0.006,f"{lab}  {val} ({val/total:.0%})",fontsize=10.2,va="center", color=COL["ink"])
    axl.set_xlim(0,1); axl.set_ylim(0,1)
    fig.subplots_adjust(left=0.04, right=0.99, top=0.95, bottom=0.07)
    return fig


# -----------------------------
# 7. Generic heatmap figures
# -----------------------------
def matrix_from_records(records, row_order, col_order, row_key, col_key, val_key, label_key=None):
    row_labels = []
    for r in row_order:
        matches=[x for x in records if x[row_key]==r]
        if matches and label_key:
            row_labels.append(matches[0].get(label_key,r))
        else:
            row_labels.append(MODEL_LABELS.get(r,r))
    col_labels=[]
    mat=[]
    for rr in row_order:
        vals=[]
        for cc in col_order:
            item=next((x for x in records if x[row_key]==rr and x[col_key]==cc), None)
            vals.append(np.nan if item is None else item[val_key])
            if len(col_labels)<len(col_order):
                col_labels.append(item.get("artifact_label", cc) if item and "artifact_label" in item else cc)
        mat.append(vals)
    return np.array(mat, dtype=float), row_labels, col_labels


def draw_heatmap_matrix(mat, row_labels, col_labels, title, cbar_label="Score", figsize=(5.4,3.2), vmin=0.15, vmax=0.80) -> plt.Figure:
    fig, ax = plt.subplots(figsize=figsize)
    im = ax.imshow(mat, cmap=HEATMAP_CMAP, vmin=vmin, vmax=vmax, aspect="auto")
    ax.set_title(title, loc="left", pad=6, fontsize=12.5)
    ax.set_xticks(np.arange(len(col_labels)))
    ax.set_xticklabels(col_labels, rotation=30, ha="right", fontsize=9.2, color=COL["ink"])
    ax.set_yticks(np.arange(len(row_labels)))
    ax.set_yticklabels(row_labels, fontsize=9.2, color=COL["ink"])
    ax.tick_params(length=0)
    for sp in ax.spines.values(): sp.set_visible(False)
    ax.set_xticks(np.arange(-.5, mat.shape[1], 1), minor=True)
    ax.set_yticks(np.arange(-.5, mat.shape[0], 1), minor=True)
    ax.grid(which="minor", color="white", linewidth=1.0)
    for i in range(mat.shape[0]):
        for j in range(mat.shape[1]):
            v=mat[i,j]
            if np.isnan(v): continue
            txt_col="white" if v > (vmin+vmax)/2 else COL["ink"]
            ax.text(j,i,f"{v:.2f}",ha="center",va="center",fontsize=8.0,color=txt_col)
    fig.subplots_adjust(bottom=0.35, top=0.92, left=0.16, right=0.98)
    cb = fig.colorbar(im, ax=ax, orientation="horizontal", fraction=0.09, pad=0.24)
    cb.set_label(cbar_label, fontsize=9.5, color=COL["ink"])
    cb.ax.tick_params(labelsize=8.5, length=0, colors=COL["ink"])
    return fig


def draw_role_heatmap(data: dict) -> plt.Figure:
    mat, rows, cols = matrix_from_records(data["data"], data["model_order"], data["column_order"], "model", "role_class", "score", "model_label")
    return draw_heatmap_matrix(mat, rows, cols, "Score by enterprise role", figsize=(5.9,4.2), vmin=0.15, vmax=0.75)


def draw_artifact_heatmap(data: dict) -> plt.Figure:
    mat, rows, cols = matrix_from_records(data["data"], data["model_order"], data["column_order"], "model", "artifact_type_bucket", "score", "model_label")
    return draw_heatmap_matrix(mat, rows, cols, "Score by deliverable type", figsize=(5.6,3.5), vmin=0.15, vmax=0.95)


def draw_dimension_profile(data: dict) -> plt.Figure:
    df = pd.DataFrame(data["data"]).sort_values("score_avg", ascending=False)
    cols = data["fields"]["values"]
    mat = df[cols].values
    rows = df["model_label"].tolist()
    return draw_heatmap_matrix(mat, rows, cols, "Semantic quality profile", figsize=(4.8,3.4), vmin=0.20, vmax=0.80)


def draw_judge_ablation(data: dict) -> plt.Figure:
    panels = data["panels"]
    text = pd.DataFrame(panels["text_judges"]["data"]).sort_values("rank_by_sonnet_main")
    visual = pd.DataFrame(panels["visual_judges"]["data"]).sort_values("rank_by_sonnet_main")
    text_cols = [c for c in panels["text_judges"]["fields"]["judges"]]
    visual_cols = [c for c in panels["visual_judges"]["fields"]["judges"]]
    fig, axes = plt.subplots(1, 2, figsize=(11.2, 9.2), gridspec_kw={"wspace":0.45})
    for ax, df, cols, title, vmin in [(axes[0], text, text_cols, "Text judges", 0.18), (axes[1], visual, visual_cols, "Visual judges", 0.28)]:
        mat = df[cols].values
        im=ax.imshow(mat, cmap=HEATMAP_CMAP, vmin=vmin, vmax=0.92, aspect="auto")
        ax.set_title(title, loc="left", pad=6, fontsize=12.5)
        ax.set_xticks(np.arange(len(cols)))
        ax.set_xticklabels(cols, rotation=35, ha="right", fontsize=9.0, color=COL["ink"])
        ax.set_yticks(np.arange(len(df)))
        ax.set_yticklabels(df["combo_label"].tolist(), fontsize=7.2, color=COL["ink"])
        ax.tick_params(length=0)
        for sp in ax.spines.values(): sp.set_visible(False)
        ax.set_xticks(np.arange(-.5, len(cols), 1), minor=True)
        ax.set_yticks(np.arange(-.5, len(df), 1), minor=True)
        ax.grid(which="minor", color="white", lw=0.6)
        for i in range(mat.shape[0]):
            for j in range(mat.shape[1]):
                v=mat[i,j]
                ax.text(j,i,f"{v:.2f}",ha="center",va="center",fontsize=6.0,color="white" if v>0.65 else COL["ink"])
        cb = fig.colorbar(im, ax=ax, orientation="horizontal", fraction=0.05, pad=0.10)
        cb.set_label("Average score", fontsize=9.0, color=COL["ink"])
        cb.ax.tick_params(labelsize=8.0, length=0, colors=COL["ink"])
    fig.subplots_adjust(bottom=0.16, top=0.96, left=0.12, right=0.98)
    return fig




if __name__ == "__main__":
    set_style()
    here = Path(__file__).resolve().parent
    with open(here / "data.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    fig = draw_pipeline(data)
    fig.savefig(here / "figure.png", dpi=220, bbox_inches="tight")
    fig.savefig(here / "figure.pdf", bbox_inches="tight")
    print("Wrote", here / "figure.png")
    print("Wrote", here / "figure.pdf")
