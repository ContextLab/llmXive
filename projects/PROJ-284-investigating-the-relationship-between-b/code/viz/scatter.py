"""
code/viz/scatter.py

Simple scatter‑plot generator used by the ``viz_report`` step. It reads the
metrics CSV, plots two chosen metrics, adds a regression line and annotates
the plot with the Spearman correlation coefficient.
"""

import os
import matplotlib.pyplot as plt
import pandas as pd
from scipy import stats

from code.logging_config import get_logger, log_operation

logger = get_logger(__name__)


@log_operation
def generate_scatter_plot(
    input: str,
    x: str,
    y: str,
    output: str,
    x_label: str | None = None,
    y_label: str | None = None,
    title: str | None = None,
) -> None:
    """
    Create a scatter plot of ``x`` vs ``y`` from ``input`` CSV and save to ``output``.
    """
    df = pd.read_csv(input)
    if x not in df.columns or y not in df.columns:
        raise ValueError(f"Columns {x} and/or {y} not found in {input}")

    plt.figure(figsize=(6, 4))
    plt.scatter(df[x], df[y], alpha=0.7, edgecolor="k")

    # Fit a simple linear regression line
    slope, intercept, r_value, p_value, _ = stats.linregress(df[x], df[y])
    line_x = np.linspace(df[x].min(), df[x].max(), 100)
    line_y = intercept + slope * line_x
    plt.plot(line_x, line_y, color="red", lw=2, label=f"r={r_value:.2f}")

    plt.xlabel(x_label or x)
    plt.ylabel(y_label or y)
    plt.title(title or f"{y} vs. {x}")
    plt.legend()

    os.makedirs(os.path.dirname(output), exist_ok=True)
    plt.tight_layout()
    plt.savefig(output, dpi=150)
    plt.close()
    logger.info("Scatter plot saved to %s", output)


def main(**kwargs):
    """
    CLI entry point used by ``code/main.py`` for the ``viz_report`` step.
    """
    generate_scatter_plot(**kwargs)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate a scatter plot.")
    parser.add_argument("--input", required=True, help="Path to CSV with metrics.")
    parser.add_argument("--x", required=True, help="Column name for x‑axis.")
    parser.add_argument("--y", required=True, help="Column name for y‑axis.")
    parser.add_argument("--output", required=True, help="File to write the PNG.")
    parser.add_argument("--x-label", default=None, help="Optional X axis label.")
    parser.add_argument("--y-label", default=None, help="Optional Y axis label.")
    parser.add_argument("--title", default=None, help="Optional plot title.")
    args = parser.parse_args()
    generate_scatter_plot(
        input=args.input,
        x=args.x,
        y=args.y,
        output=args.output,
        x_label=args.x_label,
        y_label=args.y_label,
        title=args.title,
    )