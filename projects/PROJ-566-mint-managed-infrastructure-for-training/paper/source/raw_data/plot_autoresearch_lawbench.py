#!/usr/bin/env python3
"""Draw the LawBench AutoResearch search trajectory."""

from __future__ import annotations

import csv
import re
from pathlib import Path

import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "figures" / "autoresearch_data.tsv"
OUT = ROOT / "figures" / "eval_autoresearch_lawbench.png"

BLUE = "#002BFF"
KEEP = "#DEE6FF"
GRAY = "#B7C0CC"
FULL = "#7057D2"
CONTROL = "#111111"
DARK = "#111111"
GRID = "#E3E8FF"
TEAL = "#009E9A"
AMBER = "#D98B00"


def as_float(value: str) -> float | None:
    value = value.strip()
    if not value or value == "n/a":
        return None
    match = re.match(r"[-+]?\d+(?:\.\d+)?", value)
    return float(match.group(0)) if match else None


def short_name(experiment: str) -> str:
    if experiment == "baseline":
        return "base"
    if experiment.startswith("control_"):
        return "control"
    match = re.match(r"v(\d+)", experiment)
    return f"v{match.group(1)}" if match else experiment


def main() -> None:
    with DATA.open(newline="") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))

    x = list(range(len(rows)))
    proxy = [as_float(row["proxy_avg"]) for row in rows]
    full = [as_float(row["full_avg"]) for row in rows]
    status = [row["status"] for row in rows]

    promoted = [s in {"baseline", "keep"} for s in status]
    promoted_x = [i for i, flag in enumerate(promoted) if flag and proxy[i] is not None]
    promoted_y = [proxy[i] for i in promoted_x]

    best_x: list[int] = []
    best_y: list[float] = []
    best = None
    for i, y in zip(promoted_x, promoted_y):
        if best is None or y > best:
            best = y
            best_x.append(i)
            best_y.append(y)

    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "axes.labelsize": 10,
        "xtick.labelsize": 8.5,
        "ytick.labelsize": 8.5,
    })
    fig, ax = plt.subplots(figsize=(11.2, 4.8))

    discarded_x = [i for i, y in enumerate(proxy) if y is not None and not promoted[i] and status[i] != "control"]
    ax.scatter(discarded_x, [proxy[i] for i in discarded_x], s=28, color=GRAY, edgecolor="white", linewidth=0.3, label="Proxy discarded", zorder=2)
    ax.scatter(promoted_x, promoted_y, s=48, color=KEEP, edgecolor=BLUE, linewidth=1.15, label="Proxy kept", zorder=4)

    if best_x:
        step_x = best_x + [len(rows) - 1]
        step_y = best_y + [best_y[-1]]
        ax.step(step_x, step_y, where="post", color=BLUE, linewidth=2.0, label="Proxy running best", zorder=3)

    full_x = [i for i, y in enumerate(full) if y is not None and status[i] != "control"]
    ax.scatter(full_x, [full[i] for i in full_x], s=40, color=FULL, edgecolor="#111111", linewidth=0.35, label="Full eval result", zorder=5)

    control_x = [i for i, s in enumerate(status) if s == "control" and full[i] is not None]
    if control_x:
        ax.scatter(control_x, [full[i] for i in control_x], s=58, marker="D", color=CONTROL, edgecolor=AMBER, linewidth=0.85, label="Full-manifest control", zorder=5)

    labels = {
        0: ("base", "starting point", -0.15, -0.012),
        1: ("v1", "reweighted", -1.15, 0.006),
        2: ("v2", "doc corrections", 1.25, -0.010),
        3: ("v3", "marriage disputes", -1.75, 0.006),
        10: ("v10", "lr 1e-4", -1.05, 0.006),
        24: ("v23", "more steps", -1.25, 0.008),
    }
    for i, (name, note, dx, dy) in labels.items():
        if proxy[i] is None:
            continue
        y = proxy[i]
        ax.annotate(
            f"{name}\n{note}",
            xy=(i, y),
            xytext=(i + dx, y + dy),
            color=BLUE,
            fontsize=8.2,
            fontweight="bold" if name in {"base", "v23"} else "normal",
            fontstyle="italic" if name != "base" else "normal",
            arrowprops={"arrowstyle": "-", "color": TEAL if name == "v23" else BLUE, "linewidth": 0.7},
            ha="left",
            va="center",
        )

    if control_x:
        i = control_x[0]
        ax.annotate(
            "control\nfull manifest",
            xy=(i, full[i]),
            xytext=(i - 2.15, full[i] - 0.006),
            color=CONTROL,
            fontsize=8.0,
            arrowprops={"arrowstyle": "-", "color": BLUE, "linewidth": 0.7},
            ha="left",
            va="center",
        )

    rejected_i = 11
    ax.annotate(
        "v11\nfull eval rejected",
        xy=(rejected_i, proxy[rejected_i]),
        xytext=(rejected_i + 0.95, proxy[rejected_i] - 0.006),
        color="#6B7785",
        fontsize=7.8,
        fontstyle="italic",
        arrowprops={"arrowstyle": "-", "color": "#AEB8C4", "linewidth": 0.7},
        ha="left",
        va="center",
    )

    ax.set_title("AutoResearch Progress: 26 experiments, 5 kept recipes plus base", fontsize=12.5, color=DARK, pad=12)
    ax.set_xlabel("Experiment #")
    ax.set_ylabel("LawBench score (higher is better)")
    ax.set_xlim(-0.5, len(rows) - 0.25)
    ax.set_ylim(0.458, 0.572)
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color("#C8D0D7")
    ax.tick_params(colors="#6B7785")
    ax.legend(loc="center left", bbox_to_anchor=(1.01, 0.30), frameon=False, fontsize=8.3)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, dpi=240, bbox_inches="tight", pad_inches=0.04)
    print(OUT)


if __name__ == "__main__":
    main()
