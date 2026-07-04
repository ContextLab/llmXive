"""Scaling plot generation for US-3.

Generates a PDF plot of specialization index and retrieval efficiency vs.
agent count (3, 5, 7) with fitted power-law curves and an explicit note
that 3 data points limit power-law reliability.
"""
from __future__ import annotations

import argparse
import math
import sys
import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

# Try to import matplotlib; if missing, we will generate a text-only report
try:
    import matplotlib
    matplotlib.use("Agg")  # Non-interactive backend
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False


def power_law(x: np.ndarray, a: float, b: float) -> np.ndarray:
    """Power-law function: y = a * x^b."""
    return a * np.power(x, b)


def fit_power_law(
    x: np.ndarray, y: np.ndarray
) -> Tuple[float, float, Optional[np.ndarray], Optional[np.ndarray]]:
    """Fit a power-law to data by linearizing: log(y) = log(a) + b * log(x).

    Returns:
        a, b: fitted parameters
        y_fit: predicted y values (None if fit fails)
        residuals: residuals (None if fit fails)
    """
    if len(x) < 2:
        return 1.0, 0.0, None, None

    # Filter out non-positive values for log
    mask = (x > 0) & (y > 0)
    x_fit = x[mask]
    y_fit_data = y[mask]

    if len(x_fit) < 2:
        return 1.0, 0.0, None, None

    log_x = np.log(x_fit)
    log_y = np.log(y_fit_data)

    # Linear regression
    A = np.vstack([np.ones(len(log_x)), log_x]).T
    try:
        coeffs, residuals, rank, s = np.linalg.lstsq(A, log_y, rcond=None)
    except Exception:
        return 1.0, 0.0, None, None

    log_a, b = coeffs
    a = math.exp(log_a)

    # Compute fitted values on original x
    y_pred = power_law(x, a, b)
    res = y - y_pred

    return a, b, y_pred, res


def load_scaling_data_real(input_path: Path) -> pd.DataFrame:
    """Load scaling data from a CSV file.

    Expected columns: agent_count, specialization_index, retrieval_efficiency
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Scaling data file not found: {input_path}")

    df = pd.read_csv(input_path)

    required_cols = {"agent_count", "specialization_index", "retrieval_efficiency"}
    if not required_cols.issubset(set(df.columns)):
        missing = required_cols - set(df.columns)
        raise ValueError(f"Missing required columns: {missing}")

    # Filter out non-positive values for log fitting
    df = df[(df["agent_count"] > 0) & (df["specialization_index"] >= 0) & (df["retrieval_efficiency"] >= 0)]
    return df


def generate_scaling_plot_with_notes(
    input_path: Path,
    output_path: Path,
    title: str = "Scaling of Collective Remembering Metrics",
    note_text: str = "Note: 3 data points (agent counts 3, 5, 7) limit power-law reliability.",
) -> Dict[str, Any]:
    """Generate a scaling plot with power-law fits and a reliability note.

    Args:
        input_path: Path to CSV with agent_count, specialization_index, retrieval_efficiency
        output_path: Path to output PDF
        title: Plot title
        note_text: Text note to include on the plot

    Returns:
        Dictionary with fit results and metadata
    """
    if not HAS_MATPLOTLIB:
        raise RuntimeError("matplotlib is required to generate scaling plots.")

    df = load_scaling_data_real(input_path)

    # Sort by agent_count
    df = df.sort_values("agent_count")

    agent_counts = df["agent_count"].values
    spec_indices = df["specialization_index"].values
    retrieval_effs = df["retrieval_efficiency"].values

    # Fit power laws
    a_spec, b_spec, y_spec_fit, _ = fit_power_law(agent_counts, spec_indices)
    a_ret, b_ret, y_ret_fit, _ = fit_power_law(agent_counts, retrieval_effs)

    # Create plot
    fig, ax = plt.subplots(figsize=(8, 6))

    # Plot data points
    ax.scatter(agent_counts, spec_indices, color="blue", label="Specialization Index", zorder=3)
    ax.scatter(agent_counts, retrieval_effs, color="green", label="Retrieval Efficiency", zorder=3)

    # Plot fitted curves
    x_smooth = np.linspace(min(agent_counts), max(agent_counts), 100)
    if y_spec_fit is not None:
        ax.plot(x_smooth, power_law(x_smooth, a_spec, b_spec), "b-", label=f"Specialization Fit (b={b_spec:.3f})")
    if y_ret_fit is not None:
        ax.plot(x_smooth, power_law(x_smooth, a_ret, b_ret), "g-", label=f"Retrieval Fit (b={b_ret:.3f})")

    ax.set_xlabel("Number of Agents")
    ax.set_ylabel("Metric Value")
    ax.set_title(title)
    ax.legend()
    ax.grid(True, linestyle="--", alpha=0.6)

    # Add note about 3 data points
    note_box_props = dict(boxstyle="round", facecolor="wheat", alpha=0.8)
    ax.text(
        0.02, 0.98, note_text,
        transform=ax.transAxes, fontsize=9,
        verticalalignment="top", bbox=note_box_props
    )

    # Save to PDF
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)

    return {
        "specialization": {"a": a_spec, "b": b_spec},
        "retrieval": {"a": a_ret, "b": b_ret},
        "data_points": len(agent_counts),
        "note": note_text,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate scaling plot with power-law fits.")
    parser.add_argument(
        "--input", "-i",
        type=Path,
        default=Path("data/scaling_results.csv"),
        help="Input CSV with agent_count, specialization_index, retrieval_efficiency"
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=Path("results/scaling_plot.pdf"),
        help="Output PDF path"
    )
    parser.add_argument(
        "--title", "-t",
        type=str,
        default="Scaling of Collective Remembering Metrics",
        help="Plot title"
    )
    parser.add_argument(
        "--note", "-n",
        type=str,
        default="Note: 3 data points (agent counts 3, 5, 7) limit power-law reliability.",
        help="Note text to include on the plot"
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if not HAS_MATPLOTLIB:
        print("ERROR: matplotlib is not installed. Cannot generate scaling plot.", file=sys.stderr)
        return 1

    try:
        result = generate_scaling_plot_with_notes(
            input_path=args.input,
            output_path=args.output,
            title=args.title,
            note_text=args.note,
        )
        print(f"Scaling plot generated: {args.output}")
        print(f"Specialization fit: a={result['specialization']['a']:.4f}, b={result['specialization']['b']:.4f}")
        print(f"Retrieval fit: a={result['retrieval']['a']:.4f}, b={result['retrieval']['b']:.4f}")
        print(f"Data points used: {result['data_points']}")
        return 0
    except Exception as e:
        print(f"ERROR: Failed to generate scaling plot: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())