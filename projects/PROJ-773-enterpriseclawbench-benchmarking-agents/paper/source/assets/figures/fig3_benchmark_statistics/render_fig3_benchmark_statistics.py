#!/usr/bin/env python3
from __future__ import annotations

import json
import math
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import patches

ROOT = Path(__file__).resolve().parent
DATA_PATH = ROOT / "data.json"

COL = {
    "ink": "#1B2337",
    "border": "#C9D3DE",
    "grid": "#E6EAF0",
    "neutral": "#A7B1BC",
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
    "DOC/DOCX": "#82B2AD",
    "PDF": "#E58B2E",
    "Sheet": "#A77AA3",
    "HTML": "#2E9C9A",
    "Slides": "#8FB7D8",
    "Image": "#669B4E",
    "Others": "#A7B1BA",
    "Other": "#A7B1BA",
    "Other files": "#A7B1BA",
    "Code": "#425C78",
    "Archive/package": "#51657D",
    "Skill/package": "#7C6ACF",
    "JSON": "#B9C2CC",
}

def f5(size: float) -> float:
    return size * 1.2


DONUT_CENTER_TOP_SIZE = f5(20)  # check: Figure 3 饼图中心大数字字号
DONUT_CENTER_BOTTOM_SIZE = f5(9.2)  # check: Figure 3 饼图中心说明文字字号
DONUT_TITLE_SIZE = f5(15.5)  # check: Figure 3 各子图标题字号
LEGEND_TEXT_SIZE = f5(11.2)  # check: Figure 3 图例字号（饼图右侧各项说明文字）
ROLE_LEGEND_TEXT_SIZE = f5(12.8)  # check: Figure 3A 角色分布图例字号
SUBCLASS_HEADER_SIZE = f5(12.2)  # check: Figure 3B 小类统计区表头字号
SUBCLASS_ROW_SIZE = f5(12.2)  # check: Figure 3B 每行 role class 名字号
SUBCLASS_COUNT_SIZE = f5(11.0)  # check: Figure 3B 每行 subclass 数字字号
SUBCLASS_BUBBLE_LABEL_SIZE = f5(7.2)  # check: Figure 3B 气泡上方 instance 数字字号


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


def fmt_count(x: int | float) -> str:
    return f"{int(round(x)):,}"


def display_label(label: str) -> str:
    return {"DOC/DOCX": "DOC"}.get(label, label)


def whole_percentages(values: list[int | float]) -> list[int]:
    total = sum(values)
    if total == 0:
        return [0 for _ in values]
    exact = [value * 100 / total for value in values]
    floors = [math.floor(value) for value in exact]
    remainder = 100 - sum(floors)
    order = sorted(range(len(values)), key=lambda i: exact[i] - floors[i], reverse=True)
    for i in order[:remainder]:
        floors[i] += 1
    return floors


def merge_categories(
    data: list[dict],
    label_key: str,
    value_key: str,
    merge_labels: set[str],
    merged_label: str,
) -> list[dict]:
    merged_value = 0
    out = []
    for row in data:
        label = row[label_key]
        value = row[value_key]
        if label in merge_labels:
            merged_value += value
            continue
        next_row = dict(row)
        if label in {"Other", "Other files"}:
            next_row[label_key] = merged_label
        out.append(next_row)
    if merged_value:
        for row in out:
            if row[label_key] == merged_label:
                row[value_key] += merged_value
                break
        else:
            out.append({label_key: merged_label, value_key: merged_value})
    return sorted(out, key=lambda row: row[value_key], reverse=True)


def draw_donut(
    ax: plt.Axes,
    data: list[dict],
    label_key: str,
    value_key: str,
    colors: dict[str, str],
    center_top: str,
    center_bottom: str,
    title: str,
) -> None:
    vals = [d[value_key] for d in data]
    labels = [d[label_key] for d in data]
    cols = [colors.get(label, COL["neutral"]) for label in labels]
    ax.pie(
        vals,
        startangle=90,
        counterclock=False,
        colors=cols,
        wedgeprops=dict(width=0.42, edgecolor="white", linewidth=1.0),
    )
    ax.text(0, 0.05, center_top, ha="center", va="center", fontsize=DONUT_CENTER_TOP_SIZE, weight="bold", color=COL["ink"])
    ax.text(0, -0.13, center_bottom, ha="center", va="center", fontsize=DONUT_CENTER_BOTTOM_SIZE, color=COL["ink"])
    ax.set_title(title, loc="left", fontsize=DONUT_TITLE_SIZE, pad=4)
    ax.axis("equal")
    ax.axis("off")


def match_donut_widths(reference_ax: plt.Axes, axes: list[plt.Axes]) -> None:
    target_width = reference_ax.get_position().width
    for ax in axes:
        pos = ax.get_position()
        ax.set_position([pos.x0, pos.y0, target_width, pos.height])


def render(data: dict) -> plt.Figure:
    panels = data["panels"]
    fig = plt.figure(figsize=(13.2, 7.4))
    gs = fig.add_gridspec(2, 2, width_ratios=[1.18, 1.19], height_ratios=[1, 1], wspace=0.22, hspace=0.08)

    sg = gs[0, 0].subgridspec(1, 2, width_ratios=[1.25, 1.04], wspace=0.02)
    ax_role = fig.add_subplot(sg[0, 0])
    ax_role_legend = fig.add_subplot(sg[0, 1])
    ax_role_legend.axis("off")
    role_data = panels["A_role_classes"]["data"]
    draw_donut(ax_role, role_data, "role_class", "task_count", ROLE_COLORS, "852", "tasks", "A. Role classes")
    role_percentages = whole_percentages([d["task_count"] for d in role_data])
    y = 0.90
    for d, pct in zip(role_data, role_percentages):
        role = d["role_class"]
        value = d["task_count"]
        ax_role_legend.add_patch(
            patches.Rectangle((0.02, y - 0.025), 0.035, 0.035, fc=ROLE_COLORS[role], ec="white", lw=0.5)
        )
        ax_role_legend.text(
            0.07,
            y - 0.007,
            f"{display_label(role)}  {value} ({pct}%)",
            fontsize=ROLE_LEGEND_TEXT_SIZE,
            va="center",
            color=COL["ink"],
        )
        y -= 0.092

    ax_sub = fig.add_subplot(gs[0, 1])
    ax_sub.axis("off")
    ax_sub.set_xlim(0, 1)
    ax_sub.set_ylim(0, 1)
    ax_sub.set_title("B. Skill subclasses within roles", loc="left", fontsize=DONUT_TITLE_SIZE, pad=4)
    ax_sub.text(0.46, 0.91, "subclasses", fontsize=SUBCLASS_HEADER_SIZE, weight="bold", color=COL["ink"])
    ax_sub.text(0.76, 0.91, "inst. / subclass", fontsize=SUBCLASS_HEADER_SIZE, weight="bold", color=COL["ink"])
    subclass_data = panels["B_skill_subclasses"]["data"]
    max_subclasses = max(d["subclass_count"] for d in subclass_data)
    max_instances = max(v for row in subclass_data for v in row["instance_counts_by_subclass_json"])
    y0 = 0.82
    dy = 0.105
    for i, d in enumerate(subclass_data):
        y = y0 - i * dy
        role = d["role_class"]
        color = ROLE_COLORS.get(role, COL["neutral"])
        if i > 0:
            ax_sub.plot([0, 0.985], [y + 0.05, y + 0.05], color=COL["grid"], lw=0.8)
        ax_sub.text(0.00, y, role, fontsize=SUBCLASS_ROW_SIZE, va="center", color=COL["ink"])
        bar_width = 0.18 * (d["subclass_count"] / max_subclasses)
        ax_sub.add_patch(patches.Rectangle((0.46, y - 0.017), bar_width, 0.034, fc=color, ec=color, alpha=0.9))
        ax_sub.text(0.665, y, str(d["subclass_count"]), fontsize=SUBCLASS_COUNT_SIZE, weight="bold", va="center", color=COL["ink"])
        xs = np.linspace(0.78, 0.975, len(d["instance_counts_by_subclass_json"]))
        for x, value in zip(xs, d["instance_counts_by_subclass_json"]):
            ax_sub.scatter(x, y, s=18 + 70 * (value / max_instances), color=color, edgecolor="white", lw=0.5, zorder=3)
            if value >= 26:
                ax_sub.text(x, y + 0.032, str(value), fontsize=SUBCLASS_BUBBLE_LABEL_SIZE, ha="center", color=COL["ink"])

    sg = gs[1, 0].subgridspec(1, 2, width_ratios=[1.15, 1.05], wspace=0.03)
    ax_fixture = fig.add_subplot(sg[0, 0])
    ax_fixture_legend = fig.add_subplot(sg[0, 1])
    ax_fixture_legend.axis("off")
    fixture_data = merge_categories(
        panels["C_input_fixture_files"]["display_data"],
        "fixture_type",
        "file_count",
        {"Skill/package", "JSON"},
        "Others",
    )
    fixture_colors = {
        d["fixture_type"]: FILE_COLORS.get(d["fixture_type"], COL["neutral"])
        for d in fixture_data
    }
    fixture_total = sum(d["file_count"] for d in fixture_data)
    fixture_percentages = whole_percentages([d["file_count"] for d in fixture_data])
    draw_donut(ax_fixture, fixture_data, "fixture_type", "file_count", fixture_colors, fmt_count(fixture_total), "files", "C. Input fixture files")
    y_start = 0.93
    dy = 0.092
    for idx, (d, pct) in enumerate(zip(fixture_data, fixture_percentages)):
        y = y_start - idx * dy
        label = d["fixture_type"]
        value = d["file_count"]
        ax_fixture_legend.add_patch(
            patches.Rectangle((0.02, y - 0.022), 0.028, 0.028, fc=fixture_colors[label], ec="white", lw=0.4)
        )
        ax_fixture_legend.text(
            0.06,
            y - 0.006,
            f"{display_label(label)}  {value} ({pct}%)",
            fontsize=LEGEND_TEXT_SIZE,
            va="center",
            color=COL["ink"],
        )
    ax_fixture_legend.set_xlim(0, 1)
    ax_fixture_legend.set_ylim(0, 1)

    sg = gs[1, 1].subgridspec(1, 2, width_ratios=[1.0, 1.08], wspace=0.04)
    ax_deliverable = fig.add_subplot(sg[0, 0])
    ax_deliverable_legend = fig.add_subplot(sg[0, 1])
    ax_deliverable_legend.axis("off")
    deliverable_data = merge_categories(
        panels["D_expected_deliverables"]["display_data"],
        "deliverable_type",
        "requirement_count",
        {"Skill/package", "Code", "Archive/package"},
        "Others",
    )
    deliverable_colors = {
        d["deliverable_type"]: FILE_COLORS.get(d["deliverable_type"], COL["neutral"])
        for d in deliverable_data
    }
    deliverable_total = sum(d["requirement_count"] for d in deliverable_data)
    deliverable_percentages = whole_percentages([d["requirement_count"] for d in deliverable_data])
    draw_donut(
        ax_deliverable,
        deliverable_data,
        "deliverable_type",
        "requirement_count",
        deliverable_colors,
        fmt_count(deliverable_total),
        "requirements",
        "D. Expected deliverables",
    )
    rows = int(math.ceil(len(deliverable_data) / 2))
    x_positions = [0.02, 0.70]
    y_start = 0.93
    dy = 0.118
    for idx, (d, pct) in enumerate(zip(deliverable_data, deliverable_percentages)):
        col_idx = idx // rows
        row_idx = idx % rows
        x0 = x_positions[col_idx]
        y = y_start - row_idx * dy
        label = d["deliverable_type"]
        value = d["requirement_count"]
        ax_deliverable_legend.add_patch(
            patches.Rectangle((x0, y - 0.022), 0.028, 0.028, fc=deliverable_colors[label], ec="white", lw=0.4)
        )
        ax_deliverable_legend.text(
            x0 + 0.04,
            y - 0.006,
            f"{display_label(label)}  {value} ({pct}%)",
            fontsize=LEGEND_TEXT_SIZE,
            va="center",
            color=COL["ink"],
        )
    ax_deliverable_legend.set_xlim(0, 1)
    ax_deliverable_legend.set_ylim(0, 1)

    fig.subplots_adjust(left=0.04, right=0.99, top=0.95, bottom=0.07)
    match_donut_widths(ax_deliverable, [ax_role, ax_fixture])
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
