"""Scaling plot generator for T030.

Generates `scaling_plot.pdf` with fitted power-law curves for specialization
index and retrieval efficiency vs. agent count. Includes an explicit text
note stating that "3 data points limit power-law reliability".

This script reads real experiment results from the CSV produced by
`code/run_experiment.py` (scaling run) and fits power-law models using
log-log regression. It does NOT fabricate data; if the input CSV is missing
or empty, it exits with a clear error.
"""
from __future__ import annotations

import argparse
import math
import sys
import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Ensure non-interactive backend for CI
matplotlib.use("Agg")

# Import real metrics functions from the project's metrics module
from metrics.specialization import compute_specialization_index
from metrics.retrieval import compute_retrieval_efficiency


def power_law(x: np.ndarray, a: float, b: float) -> np.ndarray:
    """Power-law function: y = a * x^b."""
    return a * np.power(x, b)


def fit_power_law_with_ci(
    x: np.ndarray, y: np.ndarray, n_boot: int = 1000
) -> Tuple[float, float, float, float]:
    """Fit a power law y = a * x^b via log-log linear regression and bootstrap CIs.

    Returns (a, b, a_ci_low, b_ci_low, a_ci_high, b_ci_high).
    If fewer than 3 points are provided, returns (None, None, None, None, None, None)
    and emits a warning.
    """
    if len(x) < 3:
        warnings.warn(
            "Fewer than 3 data points provided for power-law fit; "
            "results are unreliable. Returning None."
        )
        return (None, None, None, None, None, None)

    # Log-transform
    log_x = np.log(x)
    log_y = np.log(y)

    # Linear fit: log_y = log_a + b * log_x
    coeffs = np.polyfit(log_x, log_y, 1)
    b = coeffs[0]
    log_a = coeffs[1]
    a = math.exp(log_a)

    # Bootstrap confidence intervals
    boot_a: List[float] = []
    boot_b: List[float] = []

    rng = np.random.default_rng(42)
    for _ in range(n_boot):
        idx = rng.choice(len(x), size=len(x), replace=True)
        xb = x[idx]
        yb = y[idx]
        log_xb = np.log(xb)
        log_yb = np.log(yb)
        cb = np.polyfit(log_xb, log_yb, 1)
        boot_b.append(cb[0])
        boot_a.append(math.exp(cb[1]))

    a_ci_low, a_ci_high = np.percentile(boot_a, [2.5, 97.5])
    b_ci_low, b_ci_high = np.percentile(boot_b, [2.5, 97.5])

    return a, b, a_ci_low, b_ci_low, a_ci_high, b_ci_high


def load_scaling_data_real(csv_path: Path) -> pd.DataFrame:
    """Load real scaling results from CSV.

    Expected columns:
      agent_count, specialization_index, retrieval_efficiency

    Raises FileNotFoundError if the file does not exist.
    Raises ValueError if required columns are missing or data is empty.
    """
    if not csv_path.exists():
        raise FileNotFoundError(
            f"Scaling results CSV not found: {csv_path}. "
            "Run the scaling experiment first: "
            "python code/run_experiment.py --context full --agents 3,5,7 --games 800 --plot scaling"
        )

    df = pd.read_csv(csv_path)
    required_cols = ["agent_count", "specialization_index", "retrieval_efficiency"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(
            f"Missing required columns in {csv_path}: {missing}"
        )
    if df.empty:
        raise ValueError(f"Scaling results CSV is empty: {csv_path}")

    # Filter out rows with NaN in critical columns
    df = df.dropna(subset=required_cols)
    if df.empty:
        raise ValueError(f"All rows dropped due to NaN in required columns: {csv_path}")

    return df


def generate_scaling_plot_with_notes(
    df: pd.DataFrame,
    output_path: Path,
    note_text: str = "3 data points limit power-law reliability",
) -> None:
    """Generate scaling_plot.pdf with power-law fits and a reliability note.

    Plots:
      - specialization_index vs agent_count (with fitted power-law curve)
      - retrieval_efficiency vs agent_count (with fitted power-law curve)

    Includes a text annotation with the provided note.
    """
    agent_counts = df["agent_count"].values.astype(float)
    spec_indices = df["specialization_index"].values.astype(float)
    ret_effs = df["retrieval_efficiency"].values.astype(float)

    # Fit power laws
    a_spec, b_spec, a_spec_low, b_spec_low, a_spec_high, b_spec_high = fit_power_law_with_ci(
        agent_counts, spec_indices
    )
    a_ret, b_ret, a_ret_low, b_ret_low, a_ret_high, b_ret_high = fit_power_law_with_ci(
        agent_counts, ret_effs
    )

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    ax_spec, ax_ret = axes

    # Common x range for smooth curves
    x_min = max(1.0, agent_counts.min())
    x_max = agent_counts.max()
    x_smooth = np.linspace(x_min, x_max, 100)

    # Plot specialization
    ax_spec.scatter(agent_counts, spec_indices, color="blue", label="Observed", zorder=3)
    if a_spec is not None:
        y_smooth_spec = power_law(x_smooth, a_spec, b_spec)
        ax_spec.plot(x_smooth, y_smooth_spec, "b-", label=f"Fit: y={a_spec:.3f}·x^{b_spec:.3f}")
        ax_spec.fill_between(
            x_smooth,
            power_law(x_smooth, a_spec_low, b_spec_low),
            power_law(x_smooth, a_spec_high, b_spec_high),
            color="blue",
            alpha=0.15,
        )
    ax_spec.set_xlabel("Agent Count")
    ax_spec.set_ylabel("Specialization Index")
    ax_spec.set_title("Specialization Index vs. Agent Count")
    ax_spec.legend()
    ax_spec.grid(True, linestyle="--", alpha=0.5)

    # Plot retrieval efficiency
    ax_ret.scatter(agent_counts, ret_effs, color="green", label="Observed", zorder=3)
    if a_ret is not None:
        y_smooth_ret = power_law(x_smooth, a_ret, b_ret)
        ax_ret.plot(x_smooth, y_smooth_ret, "g-", label=f"Fit: y={a_ret:.3f}·x^{b_ret:.3f}")
        ax_ret.fill_between(
            x_smooth,
            power_law(x_smooth, a_ret_low, b_ret_low),
            power_law(x_smooth, a_ret_high, b_ret_high),
            color="green",
            alpha=0.15,
        )
    ax_ret.set_xlabel("Agent Count")
    ax_ret.set_ylabel("Retrieval Efficiency")
    ax_ret.set_title("Retrieval Efficiency vs. Agent Count")
    ax_ret.legend()
    ax_ret.grid(True, linestyle="--", alpha=0.5)

    # Add reliability note to both subplots
    for ax in (ax_spec, ax_ret):
        ax.text(
            0.02, 0.98,
            note_text,
            transform=ax.transAxes,
            fontsize=10,
            verticalalignment="top",
            bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.5),
        )

    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=150)
    plt.close(fig)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate scaling_plot.pdf with power-law fits and reliability note."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("projects/PROJ-586-social-memory-networks-modeling-collecti/results/scaling_results.csv"),
        help="Path to scaling results CSV.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("projects/PROJ-586-social-memory-networks-modeling-collecti/results/scaling_plot.pdf"),
        help="Path for output PDF.",
    )
    parser.add_argument(
        "--note",
        type=str,
        default="3 data points limit power-law reliability",
        help="Text note to display on the plot.",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    print(f"Loading scaling data from {args.input}...")
    try:
        df = load_scaling_data_real(args.input)
    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Generating plot with {len(df)} data points...")
    generate_scaling_plot_with_notes(df, args.output, args.note)
    print(f"Plot saved to {args.output}")


if __name__ == "__main__":
    main()