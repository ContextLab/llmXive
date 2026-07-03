"""Generate scaling plot with power-law fit and reliability notes."""
from __future__ import annotations

import argparse
import math
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend for CI/headless
import matplotlib.pyplot as plt

from typing import List, Optional, Tuple

@dataclass
class ScalingPlotResult:
    """Result of generating the scaling plot."""
    plot_path: Path
    exponent: float
    r_squared: float
    note: str


def power_law(x: np.ndarray, a: float, b: float) -> np.ndarray:
    """Compute power-law: y = a * x^b."""
    return a * np.power(x, b)


def load_scaling_data_real(data_path: Path) -> pd.DataFrame:
    """
    Load real scaling data from CSV.

    Expected columns:
      - agent_count: int (3, 5, 7)
      - specialization_index: float
      - retrieval_efficiency: float
    """
    if not data_path.exists():
        raise FileNotFoundError(f"Scaling data file not found: {data_path}")

    df = pd.read_csv(data_path)
    required_cols = {"agent_count", "specialization_index", "retrieval_efficiency"}
    if not required_cols.issubset(df.columns):
        missing = required_cols - set(df.columns)
        raise ValueError(f"Missing required columns in scaling data: {missing}")

    return df


def fit_power_law_with_ci(
    x: np.ndarray,
    y: np.ndarray
) -> Tuple[float, float, float]:
    """
    Fit power-law y = a * x^b via log-log linear regression.
    Returns (a, b, r_squared).

    Note: With only 3 data points, confidence intervals are unreliable.
    This function returns the point estimate and R^2 only.
    """
    if len(x) < 2:
        raise ValueError("At least 2 points required for power-law fit.")

    # Log-transform
    log_x = np.log(x)
    log_y = np.log(y)

    # Linear regression: log_y = log_a + b * log_x
    slope, intercept, r_value, _, _ = np.polyfit(log_x, log_y, 1, full=False)
    r_squared = r_value ** 2

    a = math.exp(intercept)
    b = slope

    return a, b, r_squared


def generate_scaling_plot_with_notes(
    df: pd.DataFrame,
    output_path: Path,
    title: str = "Scaling of Collective Remembering Metrics"
) -> ScalingPlotResult:
    """
    Generate scaling plot with power-law fit and explicit reliability note.

    The plot includes:
      - Specialization index vs. agent count
      - Retrieval efficiency vs. agent count
      - Fitted power-law curves
      - Explicit note that 3 data points limit power-law reliability
    """
    agent_counts = df["agent_count"].values
    spec_idx = df["specialization_index"].values
    ret_eff = df["retrieval_efficiency"].values

    # Fit power laws
    a_spec, b_spec, r2_spec = fit_power_law_with_ci(agent_counts, spec_idx)
    a_ret, b_ret, r2_ret = fit_power_law_with_ci(agent_counts, ret_eff)

    # Generate smooth curve for plotting
    x_smooth = np.linspace(min(agent_counts), max(agent_counts), 100)
    y_spec_fit = power_law(x_smooth, a_spec, b_spec)
    y_ret_fit = power_law(x_smooth, a_ret, b_ret)

    # Create plot
    fig, ax = plt.subplots(figsize=(10, 6))

    # Plot specialization index
    ax.scatter(agent_counts, spec_idx, color="blue", label="Specialization Index", zorder=5)
    ax.plot(x_smooth, y_spec_fit, color="blue", linestyle="--", label=f"Power-law fit (β={b_spec:.3f})")

    # Plot retrieval efficiency
    ax.scatter(agent_counts, ret_eff, color="red", label="Retrieval Efficiency", zorder=5)
    ax.plot(x_smooth, y_ret_fit, color="red", linestyle=":", label=f"Power-law fit (β={b_ret:.3f})")

    ax.set_xlabel("Number of Agents", fontsize=12)
    ax.set_ylabel("Metric Value", fontsize=12)
    ax.set_title(title, fontsize=14)
    ax.legend()
    ax.grid(True, alpha=0.3)

    # Add explicit note about data point limitation
    note_text = (
        "Note: Only 3 data points (N=3,5,7) are available. "
        "This limits the statistical reliability of the power-law fit. "
        "Exponents should be interpreted as preliminary estimates."
    )
    fig.text(
        0.5, 0.02,
        note_text,
        fontsize=10,
        ha="center",
        bbox=dict(facecolor="white", alpha=0.8, edgecolor="gray")
    )

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    plt.tight_layout(rect=[0, 0.1, 1, 1])
    plt.savefig(output_path, dpi=150)
    plt.close(fig)

    # Return result
    return ScalingPlotResult(
        plot_path=output_path,
        exponent=(b_spec + b_ret) / 2,  # Average exponent for summary
        r_squared=(r2_spec + r2_ret) / 2,
        note=note_text
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate scaling plot from real experiment data."
    )
    parser.add_argument(
        "--data",
        type=Path,
        default=Path("results/scaling_data.csv"),
        help="Path to scaling data CSV (default: results/scaling_data.csv)"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/scaling_plot.pdf"),
        help="Output path for PDF plot (default: results/scaling_plot.pdf)"
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        # Load real data
        df = load_scaling_data_real(args.data)

        # Generate plot
        result = generate_scaling_plot_with_notes(
            df,
            args.output,
            title="Scaling of Collective Remembering Metrics (US-3)"
        )

        print(f"Plot generated: {result.plot_path}")
        print(f"Average power-law exponent: {result.exponent:.4f}")
        print(f"R-squared: {result.r_squared:.4f}")
        print(f"Note: {result.note}")

        return 0

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
