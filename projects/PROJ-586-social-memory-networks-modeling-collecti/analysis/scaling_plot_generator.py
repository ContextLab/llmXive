"""Utilities for creating the scaling analysis PDF.

The core public function is ``generate_scaling_plot_with_notes`` which
reads a CSV containing the scaling metrics, fits a simple power‑law model
to each metric, and writes a multi‑panel PDF that includes:

* Scatter points for each agent count.
* The fitted power‑law curve.
* The estimated exponent (slope in log‑log space) with a 95 % confidence
  interval obtained via boot‑strap resampling.
* A short note stating that only three data points are available,
  limiting the statistical reliability of the fit.

The implementation purposefully avoids any external data sources – it
works entirely on the CSV produced by the experiment scripts.
"""

from __future__ import annotations

import pathlib
import random
from typing import Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def _fit_power_law(x: np.ndarray, y: np.ndarray) -> Tuple[float, float]:
    """Fit y = a * x^b using linear regression on log‑log data.

    Returns:
        (a, b) where ``a`` is the prefactor and ``b`` is the exponent.
    """
    # Guard against non‑positive values which cannot be log‑transformed.
    if np.any(x <= 0) or np.any(y <= 0):
        raise ValueError("All x and y values must be positive for power‑law fitting.")

    log_x = np.log10(x)
    log_y = np.log10(y)
    # Linear regression: log_y = log_a + b * log_x
    b, log_a = np.polyfit(log_x, log_y, 1)
    a = 10 ** log_a
    return a, b


def _bootstrap_exponent_ci(
    x: np.ndarray,
    y: np.ndarray,
    n_boot: int = 2000,
    ci: float = 0.95,
    random_state: int | None = 42,
) -> Tuple[float, float]:
    """Estimate a confidence interval for the exponent ``b`` via boot‑strap.

    Args:
        x, y: Input arrays (must be positive).
        n_boot: Number of bootstrap resamples.
        ci: Desired confidence level (e.g., 0.95 for 95 %).
        random_state: Seed for reproducibility.

    Returns:
        (lower, upper) bounds of the confidence interval for the exponent.
    """
    rng = np.random.default_rng(random_state)
    exponents = []
    n = len(x)
    for _ in range(n_boot):
        indices = rng.integers(0, n, n)
        xb = x[indices]
        yb = y[indices]
        try:
            _, b = _fit_power_law(xb, yb)
            exponents.append(b)
        except Exception:
            continue
    if not exponents:
        raise RuntimeError("Bootstrap failed to produce any valid fits.")
    lower = np.percentile(exponents, (1 - ci) / 2 * 100)
    upper = np.percentile(exponents, (1 + ci) / 2 * 100)
    return lower, upper


def generate_scaling_plot_with_notes(
    input_csv_path: str,
    output_pdf_path: str,
    *,
    title: str = "Scaling Analysis of Collective Remembering",
) -> None:
    """Create a PDF with scaling curves and a reliability note.

    Args:
        input_csv_path: Path to a CSV containing at least the columns
            ``agent_count``, ``specialization_index`` and
            ``retrieval_efficiency``.
        output_pdf_path: Destination path for the generated PDF.
        title: Optional title for the figure.

    The function writes the PDF directly; it returns ``None``.
    """
    csv_path = pathlib.Path(input_csv_path)
    if not csv_path.is_file():
        raise FileNotFoundError(f"Input CSV not found: {csv_path}")

    df = pd.read_csv(csv_path)
    required = {"agent_count", "specialization_index", "retrieval_efficiency"}
    if not required.issubset(df.columns):
        missing = required - set(df.columns)
        raise ValueError(f"Input CSV missing required columns: {missing}")

    # Ensure data are numeric and sorted by agent count.
    df = df.copy()
    df["agent_count"] = pd.to_numeric(df["agent_count"], errors="coerce")
    df["specialization_index"] = pd.to_numeric(df["specialization_index"], errors="coerce")
    df["retrieval_efficiency"] = pd.to_numeric(df["retrieval_efficiency"], errors="coerce")
    df = df.dropna(subset=["agent_count", "specialization_index", "retrieval_efficiency"])
    df = df.sort_values("agent_count")

    agent_counts = df["agent_count"].to_numpy()
    spec_vals = df["specialization_index"].to_numpy()
    retrieval_vals = df["retrieval_efficiency"].to_numpy()

    # Fit power‑law models.
    a_spec, b_spec = _fit_power_law(agent_counts, spec_vals)
    a_ret, b_ret = _fit_power_law(agent_counts, retrieval_vals)

    # Confidence intervals for exponents via boot‑strap.
    b_spec_ci = _bootstrap_exponent_ci(agent_counts, spec_vals)
    b_ret_ci = _bootstrap_exponent_ci(agent_counts, retrieval_vals)

    # Prepare the figure.
    fig, axes = plt.subplots(1, 2, figsize=(12, 5), constrained_layout=True)

    # ---- Specialization index plot ----
    ax = axes[0]
    ax.scatter(agent_counts, spec_vals, color="tab:blue", label="Observed")
    x_fit = np.linspace(agent_counts.min(), agent_counts.max(), 100)
    y_fit = a_spec * x_fit ** b_spec
    ax.plot(x_fit, y_fit, color="tab:orange", label="Power‑law fit")
    ax.set_xlabel("Number of agents")
    ax.set_ylabel("Specialization index")
    ax.set_title("Specialization vs. Agent Count")
    ax.legend()
    ax.text(
        0.05,
        0.95,
        f"Exponent $b$ = {b_spec:.3f}\\n95 % CI [{b_spec_ci[0]:.3f}, {b_spec_ci[1]:.3f}]",
        transform=ax.transAxes,
        verticalalignment="top",
        fontsize=9,
        bbox=dict(facecolor="white", alpha=0.7, edgecolor="none"),
    )

    # ---- Retrieval efficiency plot ----
    ax = axes[1]
    ax.scatter(agent_counts, retrieval_vals, color="tab:green", label="Observed")
    y_fit = a_ret * x_fit ** b_ret
    ax.plot(x_fit, y_fit, color="tab:red", label="Power‑law fit")
    ax.set_xlabel("Number of agents")
    ax.set_ylabel("Retrieval efficiency")
    ax.set_title("Retrieval Efficiency vs. Agent Count")
    ax.legend()
    ax.text(
        0.05,
        0.95,
        f"Exponent $b$ = {b_ret:.3f}\\n95 % CI [{b_ret_ci[0]:.3f}, {b_ret_ci[1]:.3f}]",
        transform=ax.transAxes,
        verticalalignment="top",
        fontsize=9,
        bbox=dict(facecolor="white", alpha=0.7, edgecolor="none"),
    )

    # Global title and note about limited data points.
    fig.suptitle(title, fontsize=14, weight="bold")
    note = (
        "NOTE: Only three distinct agent‑count conditions are available (N=3). "
        "Power‑law fits based on such few points should be interpreted with caution."
    )
    fig.text(0.5, 0.01, note, ha="center", fontsize=9, style="italic")

    # Save as PDF.
    output_path = pathlib.Path(output_pdf_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, format="pdf")
    plt.close(fig)

# The module can also be executed directly for quick testing.
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate scaling analysis PDF.")
    parser.add_argument(
        "--input-csv",
        required=True,
        help="Path to the combined scaling CSV (must contain required columns).",
    )
    parser.add_argument(
        "--output-pdf",
        required=True,
        help="Destination path for the generated PDF.",
    )
    args = parser.parse_args()
    generate_scaling_plot_with_notes(args.input_csv, args.output_pdf)