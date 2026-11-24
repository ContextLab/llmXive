"""
Simple visualisation utilities for the heterogeneity impact study.

The original project expected two PNG files:

* ``coverage_vs_tau2.png`` – coverage rate as a function of τ².
* ``mean_bias_vs_tau2.png`` – mean bias as a function of τ².

For the purposes of the integration test we generate straightforward
line‑plots using ``matplotlib``.  The data are read from the
``aggregated_metrics.csv`` file that the aggregation step produces.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

def _draw_plot(x, y, ylabel, title, out_path: Path) -> None:
    """Utility that creates a simple line plot and saves it as PNG."""
    plt.figure(figsize=(6, 4))
    plt.plot(x, y, marker="o", linestyle="-")
    plt.xlabel(r"$\tau^2$")
    plt.ylabel(ylabel)
    plt.title(title)
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()
    log.info(f"Plot saved to {out_path}")

def main() -> None:
    """
    Generate the two required PNG figures.

    The function assumes that ``data/results/aggregated_metrics.csv`` has
    already been created by the aggregation step.  If the file is missing,
    an informative ``FileNotFoundError`` is raised – this is intentional
    because the pipeline should never silently succeed with empty output.
    """
    aggregated_path = paths.results("aggregated_metrics.csv")
    if not aggregated_path.is_file():
        raise FileNotFoundError(f"Aggregated metrics file not found: {aggregated_path}")

    df = pd.read_csv(aggregated_path)

    # -------------------------------------------------------------
    # Coverage vs τ²
    # -------------------------------------------------------------
    coverage_path = paths.results("coverage_vs_tau2.png")
    _draw_plot(
        x=df["tau2_level"],
        y=df["coverage_rate"],
        ylabel="Coverage Rate",
        title="Coverage vs. τ²",
        out_path=coverage_path,
    )

    # -------------------------------------------------------------
    # Mean bias vs τ²
    # -------------------------------------------------------------
    bias_path = paths.results("mean_bias_vs_tau2.png")
    _draw_plot(
        x=df["tau2_level"],
        y=df["mean_bias"],
        ylabel="Mean Bias",
        title="Mean Bias vs. τ²",
        out_path=bias_path,
    )
