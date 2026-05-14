#!/usr/bin/env python3
"""Draw the measured N=3 GRPO schedule timeline used by Figure 8."""

from __future__ import annotations

import csv
from datetime import datetime, timezone
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Patch


ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "raw_data" / "e2_phase_timing"
SUMMARY = ROOT / "raw_data" / "e2_grpo3_gpu_utilization" / "summary.csv"
OUT = ROOT / "figures" / "eval_n3_schedule_timeline.png"

COLORS = {
    "rollout": "#002BFF",
    "update": "#009E9A",
    "eval": "#7057D2",
    "final": "#7A828C",
    "saved": "#E8F0FF",
    "seq": "#4A4A4A",
    "mint": "#002BFF",
    "grid": "#D8E2FF",
    "divider": "#AFC0FF",
}


def parse_utc(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def minutes_since(value: str, start: datetime) -> float:
    return (parse_utc(value) - start).total_seconds() / 60.0


def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def load_summary() -> dict[tuple[str, str], dict[str, float]]:
    summary: dict[tuple[str, str], dict[str, float]] = {}
    for row in load_rows(SUMMARY):
        summary[(row["model"], row["schedule"])] = {
            "wall_s": float(row["wall_time_seconds"]),
            "wall_m": float(row["wall_time_minutes"]),
            "peak_gib": float(row["peak_memory_used_gib"]),
            "avg_util": float(row["avg_gpu_util_percent"]),
            "idle_lt10": float(row["idle_fraction_lt10pct"]) * 100.0,
        }
    return summary


def schedule_start(task_rows: list[dict[str, str]], model: str, schedule: str) -> datetime:
    starts = [
        parse_utc(row["task_start_utc"])
        for row in task_rows
        if row["model"] == model and row["num_policies"] == "3" and row["schedule"] == schedule
    ]
    return min(starts)


def plot_schedule(ax, model: str, task_rows: list[dict[str, str]], step_rows: list[dict[str, str]], summary):
    schedules = ["sequential", "concurrent"]
    schedule_labels = {"sequential": "Seq.", "concurrent": "MinT"}
    y_base = {"sequential": 3.75, "concurrent": 0.35}
    y_step = 0.58
    bar_h = 0.34
    policy_names = {"grpo_a": "P1", "grpo_b": "P2", "grpo_c": "P3"}

    starts = {schedule: schedule_start(task_rows, model, schedule) for schedule in schedules}

    seq_wall = summary[(model, "sequential")]["wall_m"]
    conc_wall = summary[(model, "concurrent")]["wall_m"]
    saved = seq_wall - conc_wall
    speedup = seq_wall / conc_wall
    peak_seq = summary[(model, "sequential")]["peak_gib"]
    peak_conc = summary[(model, "concurrent")]["peak_gib"]

    ax.axvspan(conc_wall, seq_wall, color=COLORS["saved"], zorder=0)

    for schedule in schedules:
        start = starts[schedule]
        for idx, task in enumerate(["grpo_a", "grpo_b", "grpo_c"]):
            y = y_base[schedule] + (2 - idx) * y_step
            for row in step_rows:
                if (
                    row["model"] == model
                    and row["num_policies"] == "3"
                    and row["schedule"] == schedule
                    and row["task"] == task
                ):
                    step_start = minutes_since(row["step_start_utc"], start)
                    rollout_done = minutes_since(row["rollout_done_utc"], start)
                    step_done = minutes_since(row["step_done_utc"], start)
                    ax.barh(
                        y,
                        rollout_done - step_start,
                        left=step_start,
                        height=bar_h,
                        color=COLORS["rollout"],
                        edgecolor="white",
                        linewidth=0.35,
                    )
                    ax.barh(
                        y,
                        step_done - rollout_done,
                        left=rollout_done,
                        height=bar_h,
                        color=COLORS["update"],
                        edgecolor="white",
                        linewidth=0.35,
                    )

            task_row = next(
                row
                for row in task_rows
                if (
                    row["model"] == model
                    and row["num_policies"] == "3"
                    and row["schedule"] == schedule
                    and row["task"] == task
                )
            )
            train_end = minutes_since(task_row["train_end_utc"], start)
            eval_done = minutes_since(task_row["eval_done_utc"], start)
            task_end = minutes_since(task_row["task_end_utc"], start)
            if eval_done > train_end:
                ax.barh(
                    y,
                    eval_done - train_end,
                    left=train_end,
                    height=bar_h,
                    color=COLORS["eval"],
                    edgecolor="white",
                    linewidth=0.35,
                )
            if task_end > eval_done:
                ax.barh(
                    y,
                    task_end - eval_done,
                    left=eval_done,
                    height=bar_h,
                    color=COLORS["final"],
                    edgecolor="white",
                    linewidth=0.35,
                )

    ax.axvline(conc_wall, color=COLORS["mint"], linestyle=(0, (4, 3)), linewidth=1.2)
    ax.axvline(seq_wall, color=COLORS["seq"], linestyle=(0, (4, 3)), linewidth=1.2)
    ax.text(conc_wall, 5.55, f"MinT done\n{conc_wall:.1f} min", ha="right", va="bottom", fontsize=7.2, color=COLORS["mint"])
    ax.text(seq_wall, 5.55, f"Seq. done\n{seq_wall:.1f} min", ha="right", va="bottom", fontsize=7.2, color=COLORS["seq"])

    y_ticks = []
    y_labels = []
    for schedule in schedules:
        for idx, task in enumerate(["grpo_a", "grpo_b", "grpo_c"]):
            y_ticks.append(y_base[schedule] + (2 - idx) * y_step)
            y_labels.append(f"{schedule_labels[schedule]} {policy_names[task]}")
    ax.set_yticks(y_ticks)
    ax.set_yticklabels(y_labels, fontsize=7.4)
    ax.set_xlim(0, seq_wall * 1.03)
    ax.set_ylim(-0.05, 6.05)
    ax.set_xlabel("Elapsed time (minutes)")
    ax.set_title(model, loc="left", fontsize=10, fontweight="bold")
    ax.grid(axis="x", color=COLORS["grid"], linewidth=0.7)
    ax.set_axisbelow(True)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.tick_params(axis="y", length=0)
    ax.axhline(3.25, color=COLORS["divider"], linewidth=0.8)
    ax.text(
        0.985,
        0.08,
        f"{seq_wall:.1f} -> {conc_wall:.1f} min\n"
        f"{speedup:.2f}x faster, {saved:.1f} min saved\n"
        f"peak memory {peak_seq:.1f} -> {peak_conc:.1f} GiB",
        transform=ax.transAxes,
        ha="right",
        va="bottom",
        fontsize=7.6,
        bbox={"boxstyle": "round,pad=0.35", "facecolor": "white", "edgecolor": COLORS["divider"], "linewidth": 0.8},
    )


def plot_metric_bars(ax, summary, metric: str, title: str, xlim: float, suffix: str) -> None:
    models = ["Qwen3-4B", "Qwen3-30B"]
    y_centers = [1.0, 0.0]
    offsets = [0.16, -0.16]
    schedules = [("sequential", "Seq.", COLORS["seq"]), ("concurrent", "MinT", COLORS["mint"])]

    for y, model in zip(y_centers, models):
        for offset, (schedule, label, color) in zip(offsets, schedules):
            value = summary[(model, schedule)][metric]
            ax.barh(y + offset, value, height=0.24, color=color, edgecolor="white", linewidth=0.4)
            if value > xlim * 0.78:
                label_x = value - xlim * 0.018
                label_ha = "right"
                label_color = "white"
            else:
                label_x = value + xlim * 0.018
                label_ha = "left"
                label_color = "#111111"
            ax.text(
                label_x,
                y + offset,
                f"{value:.1f}{suffix}",
                va="center",
                ha=label_ha,
                fontsize=7.1,
                color=label_color,
            )

    ax.set_title(title, loc="left", fontsize=8.4, fontweight="bold")
    ax.set_xlim(0, xlim)
    ax.set_yticks(y_centers)
    ax.set_yticklabels(models, fontsize=7.4)
    ax.grid(axis="x", color=COLORS["grid"], linewidth=0.65)
    ax.set_axisbelow(True)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.tick_params(axis="y", length=0)
    ax.tick_params(axis="x", labelsize=7.0)


def plot_resource_row(axes, summary) -> None:
    plot_metric_bars(axes[0], summary, "avg_util", "Avg GPU util.", 45.0, "%")
    plot_metric_bars(axes[1], summary, "idle_lt10", "Idle samples, GPU util. <10%", 100.0, "%")
    plot_metric_bars(axes[2], summary, "peak_gib", "Peak memory used", 75.0, " GiB")
    axes[1].set_yticklabels([])
    axes[2].set_yticklabels([])
    handles = [
        Patch(facecolor=COLORS["seq"], label="Sequential"),
        Patch(facecolor=COLORS["mint"], label="Concurrent MinT"),
    ]
    axes[2].legend(handles=handles, loc="upper right", bbox_to_anchor=(1.0, 1.52), ncol=2, frameon=False, fontsize=7.0)


def main() -> None:
    task_rows = load_rows(DATA / "task_phase_summary.csv")
    step_rows = load_rows(DATA / "step_phase_summary.csv")
    summary = load_summary()

    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "axes.labelsize": 9,
        "xtick.labelsize": 8,
    })
    fig = plt.figure(figsize=(10.8, 5.85), constrained_layout=False)
    gs = fig.add_gridspec(3, 3, height_ratios=[1.0, 1.0, 0.50], hspace=0.52, wspace=0.28)
    timeline_axes = [fig.add_subplot(gs[0, :]), fig.add_subplot(gs[1, :])]
    resource_axes = [fig.add_subplot(gs[2, idx]) for idx in range(3)]
    for ax, model in zip(timeline_axes, ["Qwen3-4B", "Qwen3-30B"]):
        plot_schedule(ax, model, task_rows, step_rows, summary)
    plot_resource_row(resource_axes, summary)

    handles = [
        Patch(facecolor=COLORS["rollout"], label="Rollout / sampling"),
        Patch(facecolor=COLORS["update"], label="Update"),
        Patch(facecolor=COLORS["eval"], label="Evaluation"),
        Patch(facecolor=COLORS["final"], label="Post-eval finalize"),
        Patch(facecolor=COLORS["saved"], label="Wall time saved"),
    ]
    fig.legend(handles=handles, loc="upper center", ncol=5, frameon=False, bbox_to_anchor=(0.5, 0.985), fontsize=7.9)
    fig.text(0.15, 0.235, "Resource telemetry from the same N=3 runs", fontsize=8.4, fontweight="bold")
    fig.subplots_adjust(top=0.89, left=0.105, right=0.99, bottom=0.075)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, dpi=220, bbox_inches="tight", pad_inches=0.02)
    print(OUT)


if __name__ == "__main__":
    main()
