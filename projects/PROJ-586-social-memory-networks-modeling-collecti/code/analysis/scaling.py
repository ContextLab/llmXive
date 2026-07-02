"""Scaling analysis utilities.

The ``generate_scaling_plot`` function reads the per‑agent CSV files produced
by ``run_experiment.py`` (for the scaling user story) and fits a simple
power‑law (y = a * x^b) to each metric across the three agent counts.
The resulting curves are plotted and saved as a PDF.
"""

from __future__ import annotations

import pathlib
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.optimize import curve_fit


def _power_law(x: np.ndarray, a: float, b: float) -> np.ndarray:
    """Power‑law function a * x^b."""
    return a * np.power(x, b)


def generate_scaling_plot(
    results_dir: Path | str,
    output_path: Path | str,
) -> None:
    """Generate a scaling PDF plot for specialization index and retrieval efficiency.

    Parameters
    ----------
    results_dir:
        Directory containing ``results_scaling_<agent_count>.csv`` files.
    output_path:
        Destination PDF file for the plot.
    """
    results_dir = Path(results_dir)
    output_path = Path(output_path)

    # Load all CSVs that match the naming convention.
    csv_files = sorted(results_dir.glob("results_scaling_*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"No scaling result CSVs found in {results_dir}")

    # Aggregate data per metric.
    data = {
        "agent_count": [],
        "specialization_index": [],
        "retrieval_efficiency": [],
    }
    for csv_file in csv_files:
        df = pd.read_csv(csv_file)
        # All rows have the same agent_count; take the first.
        agent_cnt = int(df["agent_count"].iloc[0])
        data["agent_count"].append(agent_cnt)
        data["specialization_index"].append(df["specialization_index"].mean())
        data["retrieval_efficiency"].append(df["retrieval_efficiency"].mean())

    # Convert to numpy arrays for fitting.
    x = np.array(data["agent_count"], dtype=float)
    spec_y = np.array(data["specialization_index"], dtype=float)
    retr_y = np.array(data["retrieval_efficiency"], dtype=float)

    # Fit power‑law curves.
    spec_params, _ = curve_fit(_power_law, x, spec_y, p0=(1.0, 0.5))
    retr_params, _ = curve_fit(_power_law, x, retr_y, p0=(1.0, 0.5))

    # Plotting.
    fig, ax1 = plt.subplots(figsize=(8, 5))

    ax1.set_xlabel("Number of agents")
    ax1.set_ylabel("Specialization index", color="tab:blue")
    ax1.scatter(x, spec_y, color="tab:blue", label="Specialization (data)")
    ax1.plot(
        x,
        _power_law(x, *spec_params),
        color="tab:blue",
        linestyle="--",
        label=f"Fit: a·N^b (b={spec_params[1]:.2f})",
    )
    ax1.tick_params(axis="y", labelcolor="tab:blue")

    ax2 = ax1.twinx()
    ax2.set_ylabel("Retrieval efficiency", color="tab:red")
    ax2.scatter(x, retr_y, color="tab:red", label="Retrieval (data)")
    ax2.plot(
        x,
        _power_law(x, *retr_params),
        color="tab:red",
        linestyle="--",
        label=f"Fit: a·N^b (b={retr_params[1]:.2f})",
    )
    ax2.tick_params(axis="y", labelcolor="tab:red")

    # Combine legends.
    lines, labels = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines + lines2, labels + labels2, loc="upper left")

    plt.title(
        "Scaling of specialization index and retrieval efficiency vs. agent count"
    )
    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path)
    plt.close(fig)