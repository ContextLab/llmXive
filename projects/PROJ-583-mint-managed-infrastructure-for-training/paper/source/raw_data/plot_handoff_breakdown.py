from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Patch


OUT = Path(__file__).resolve().parents[1] / "figures" / "eval_handoff_breakdown.png"

MINDLAB_BLUE = "#002BFF"
ROLL_OUT = "#009E9A"
INK = "#111111"
MUTED = "#4A4A4A"
GRID = "#D9E1F2"
CALLOUT = "#F4F6FF"

panels = [
    {
        "title": "Qwen3-4B",
        "ylim": 82,
        "yticks": range(0, 81, 20),
        "materialize": [0.036, 71.820],
        "rollout": [4.114, 3.080],
        "totals": [4.1, 74.9],
        "adapter_label_dx": -0.18,
    },
    {
        "title": "Qwen3-30B",
        "ylim": 650,
        "yticks": range(0, 651, 100),
        "materialize": [46.455, 402.245],
        "rollout": [162.245, 193.255],
        "totals": [208.7, 595.5],
        "adapter_label_dx": -0.06,
    },
]


def add_speedup(ax, x, y_low, y_high, label):
    ax.annotate(
        "",
        xy=(x, y_low),
        xytext=(x, y_high),
        arrowprops=dict(arrowstyle="<->", color=INK, lw=1.8, shrinkA=4, shrinkB=4),
    )
    ax.text(
        x + 0.16,
        (y_low + y_high) / 2,
        label,
        ha="left",
        va="center",
        fontsize=11,
        fontweight="bold",
        color=MINDLAB_BLUE,
        bbox=dict(boxstyle="round,pad=0.16", fc=CALLOUT, ec=MINDLAB_BLUE, lw=0.8),
    )


plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "axes.titlesize": 22,
        "axes.labelsize": 16,
        "xtick.labelsize": 16,
        "ytick.labelsize": 14,
        "legend.fontsize": 14,
    }
)

fig, axes = plt.subplots(1, 2, figsize=(12.8, 4.9), dpi=130)

for ax, panel in zip(axes, panels):
    xs = [0, 1]
    width = 0.55
    materialize = panel["materialize"]
    rollout = panel["rollout"]
    totals = panel["totals"]
    speedup = totals[1] / totals[0]

    ax.bar(xs, materialize, width=width, color=MINDLAB_BLUE, edgecolor="none")
    ax.bar(xs, rollout, bottom=materialize, width=width, color=ROLL_OUT, edgecolor="none")
    ax.plot(
        [xs[0], xs[1] - width / 2],
        [totals[1], totals[1]],
        color=INK,
        linewidth=1.1,
        linestyle=(0, (3, 3)),
        alpha=0.45,
        zorder=1,
    )

    ax.set_title(panel["title"], pad=8)
    ax.set_xticks(xs, ["Adapter", "Merge"])
    ax.set_ylabel("wall time (s)")
    ax.set_ylim(0, panel["ylim"])
    ax.set_yticks(list(panel["yticks"]))
    ax.grid(axis="y", color=GRID, linewidth=1.0)
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(INK)
    ax.spines["bottom"].set_color(INK)
    ax.spines["left"].set_linewidth(1.2)
    ax.spines["bottom"].set_linewidth(1.2)
    ax.tick_params(axis="both", colors=INK, width=1.0, length=5)

    for i, (x, total) in enumerate(zip(xs, totals)):
        if i == 0:
            text_x = x + panel["adapter_label_dx"]
            ha = "right"
        else:
            text_x = x
            ha = "center"
        ax.text(
            text_x,
            total + panel["ylim"] * 0.035,
            f"{total:.1f}s",
            ha=ha,
            va="bottom",
            fontsize=14,
            color=MUTED,
            fontweight="bold",
        )

    add_speedup(ax, xs[0], totals[0], totals[1], f"{speedup:.1f}x faster")

legend_handles = [
    Patch(facecolor=MINDLAB_BLUE, label="materialize / admit"),
    Patch(facecolor=ROLL_OUT, label="rollout"),
]
fig.legend(
    handles=legend_handles,
    loc="upper center",
    bbox_to_anchor=(0.5, 1.02),
    ncol=2,
    frameon=False,
)

fig.tight_layout(w_pad=2.6, rect=(0, 0, 1, 0.94))
fig.savefig(OUT, facecolor="white", bbox_inches="tight", pad_inches=0.08)
print(f"Wrote {OUT}")
