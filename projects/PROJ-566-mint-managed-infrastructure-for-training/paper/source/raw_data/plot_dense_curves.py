import csv
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "figures" / "eval_dense_curves.png"
BLUE = "#002BFF"
GRID = "#DAE0FF"
INK = "#111111"


def read_csv(path: Path, x_key: str, y_key: str) -> tuple[list[float], list[float]]:
    rows = list(csv.DictReader(path.open(newline="")))
    if not rows:
        raise RuntimeError(f"{path} has no data rows")
    xs: list[float] = []
    ys: list[float] = []
    for row in rows:
        xs.append(float(row[x_key]))
        ys.append(float(row[y_key]))
    return xs, ys


def read_dpo_margin(path: Path) -> tuple[list[float], list[float]]:
    xs: list[float] = []
    ys: list[float] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        if not raw.strip():
            continue
        row = json.loads(raw)
        xs.append(float(row["step"]))
        ys.append(float(row["margin"]))
    if not xs:
        raise RuntimeError(f"{path} has no metric rows")
    return xs, ys


def style(ax: plt.Axes) -> None:
    ax.grid(axis="y", color=GRID, linewidth=1.0)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(INK)
        ax.spines[side].set_linewidth(1.0)
    ax.tick_params(axis="both", colors=INK, width=1.0, length=5)
    ax.title.set_color(INK)
    ax.xaxis.label.set_color(INK)
    ax.yaxis.label.set_color(INK)


def main() -> None:
    sft_x, sft_y = read_csv(
        ROOT / "raw_data" / "dense_curves" / "fingpt_fineval_train_loss.csv",
        "step",
        "train_mean_nll",
    )
    dpo_x, dpo_y = read_dpo_margin(
        ROOT / "raw_data" / "leixiang_chat_dpo" / "metrics.jsonl"
    )
    grpo_x, grpo_y = read_csv(
        ROOT / "raw_data" / "dense_curves" / "dapo_aime24_accuracy.csv",
        "step",
        "train_accuracy_ema",
    )

    fig, axes = plt.subplots(1, 3, figsize=(10.9, 3.25), dpi=220)

    axes[0].plot(sft_x, sft_y, color=BLUE, linewidth=2.2)
    axes[0].set_title("SFT: Fineval", fontsize=13, pad=8)
    axes[0].set_xlabel("optimizer step", fontsize=10.5)
    axes[0].set_ylabel("train loss", fontsize=10.5)
    axes[0].set_ylim(0, 0.95)

    axes[1].plot(dpo_x, dpo_y, color=BLUE, linewidth=2.2)
    axes[1].set_title("DPO: chat pairs", fontsize=13, pad=8)
    axes[1].set_xlabel("optimizer step", fontsize=10.5)
    axes[1].set_ylabel("reward margin", fontsize=10.5)
    axes[1].set_ylim(-1.5, 32.5)

    axes[2].plot(grpo_x, grpo_y, color=BLUE, linewidth=2.2)
    axes[2].set_title("GRPO: DAPO-AIME24 (8B)", fontsize=13, pad=8)
    axes[2].set_xlabel("GRPO step", fontsize=10.5)
    axes[2].set_ylabel("train accuracy (EMA)", fontsize=10.5)
    axes[2].set_ylim(0.08, 0.52)

    for ax in axes:
        style(ax)

    fig.tight_layout(w_pad=2.0)
    fig.savefig(OUT, facecolor="white", bbox_inches="tight", pad_inches=0.08)


if __name__ == "__main__":
    main()
