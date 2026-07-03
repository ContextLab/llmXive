"""Scaling plot generator for User Story 3 (T030).

Generates scaling_plot.pdf with fitted power-law curves and an explicit note
that 3 data points limit power-law reliability.
"""
from __future__ import annotations

import argparse
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np
import pandas as pd

# Try to import matplotlib; if not available, we'll use a fallback
try:
    import matplotlib
    matplotlib.use("Agg")  # Non-interactive backend
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False


@dataclass
class ScalingPlotResult:
    """Result of scaling plot generation."""
    success: bool
    output_path: str
    message: str
    power_law_exponent: Optional[float] = None


def power_law(x: np.ndarray, a: float, b: float) -> np.ndarray:
    """Power law function: y = a * x^b."""
    return a * np.power(x, b)


def fit_power_law_safe(
    x: np.ndarray, y: np.ndarray
) -> Tuple[Optional[float], Optional[float], Optional[float]]:
    """Fit power law y = a * x^b using log-log linear regression.

    Returns (a, b, r_squared) or (None, None, None) if fitting fails.
    """
    if len(x) < 2:
        return None, None, None

    # Avoid log(0)
    mask = (x > 0) & (y > 0)
    if np.sum(mask) < 2:
        return None, None, None

    x_log = np.log(x[mask])
    y_log = np.log(y[mask])

    # Linear regression: y_log = log(a) + b * x_log
    # Use numpy's polyfit for simplicity
    try:
        coeffs = np.polyfit(x_log, y_log, 1)
        b = coeffs[0]  # exponent
        log_a = coeffs[1]
        a = math.exp(log_a)

        # Compute R^2
        y_pred = np.polyval(coeffs, x_log)
        ss_res = np.sum((y_log - y_pred) ** 2)
        ss_tot = np.sum((y_log - np.mean(y_log)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0.0

        return a, b, r_squared
    except Exception:
        return None, None, None


def load_scaling_data_from_csv(input_path: Path) -> pd.DataFrame:
    """Load scaling data from CSV.

    Expected columns: agent_count, specialization_index, retrieval_efficiency
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    df = pd.read_csv(input_path)
    required_cols = ["agent_count", "specialization_index", "retrieval_efficiency"]
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    return df


def generate_scaling_plot_with_notes(
    input_path: Path,
    output_path: Path,
    note_text: str = "Note: 3 data points limit power-law reliability.",
) -> ScalingPlotResult:
    """Generate scaling plot with power-law fits and reliability note.

    Args:
        input_path: Path to input CSV with scaling data.
        output_path: Path to output PDF.
        note_text: Text note about data limitations.

    Returns:
        ScalingPlotResult with success status and details.
    """
    if not HAS_MATPLOTLIB:
        return ScalingPlotResult(
            success=False,
            output_path=str(output_path),
            message="matplotlib not available; cannot generate plot.",
        )

    try:
        # Load data
        df = load_scaling_data_from_csv(input_path)

        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Extract data
        agent_counts = df["agent_count"].values
        spec_indices = df["specialization_index"].values
        ret_effs = df["retrieval_efficiency"].values

        # Sort by agent count for consistent plotting
        sort_idx = np.argsort(agent_counts)
        agent_counts = agent_counts[sort_idx]
        spec_indices = spec_indices[sort_idx]
        ret_effs = ret_effs[sort_idx]

        # Fit power laws
        a_spec, b_spec, r2_spec = fit_power_law_safe(agent_counts, spec_indices)
        a_ret, b_ret, r2_ret = fit_power_law_safe(agent_counts, ret_effs)

        # Create figure
        fig, ax = plt.subplots(figsize=(10, 6))

        # Plot specialization index
        ax.scatter(agent_counts, spec_indices, color='blue', label='Specialization Index', zorder=5)
        if a_spec is not None and b_spec is not None:
            x_fit = np.linspace(min(agent_counts), max(agent_counts), 100)
            y_fit = power_law(x_fit, a_spec, b_spec)
            ax.plot(x_fit, y_fit, 'b--', label=f'Power-law fit (β={b_spec:.3f})')

        # Plot retrieval efficiency (secondary axis)
        ax2 = ax.twinx()
        ax2.scatter(agent_counts, ret_effs, color='red', label='Retrieval Efficiency', zorder=5)
        if a_ret is not None and b_ret is not None:
            y_fit_ret = power_law(x_fit, a_ret, b_ret)
            ax2.plot(x_fit, y_fit_ret, 'r--', label=f'Power-law fit (β={b_ret:.3f})')

        # Labels and title
        ax.set_xlabel('Number of Agents (N)', fontsize=12)
        ax.set_ylabel('Specialization Index', color='blue', fontsize=12)
        ax2.set_ylabel('Retrieval Efficiency', color='red', fontsize=12)
        ax.set_title('Scaling of Collective Remembering Metrics', fontsize=14)

        # Combine legends from both axes
        lines1, labels1 = ax.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax.legend(lines1 + lines2, labels1 + labels2, loc='best')

        # Add reliability note
        fig.text(
            0.5, 0.02,
            note_text,
            ha='center',
            va='bottom',
            fontsize=10,
            style='italic',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5)
        )

        # Save to PDF
        plt.tight_layout()
        plt.savefig(output_path, format='pdf', dpi=300)
        plt.close()

        # Determine success
        success = True
        message = f"Plot generated successfully. Power-law exponents: Spec={b_spec:.3f}, Ret={b_ret:.3f}"

        return ScalingPlotResult(
            success=success,
            output_path=str(output_path),
            message=message,
            power_law_exponent=b_spec if b_spec is not None else b_ret
        )

    except Exception as e:
        return ScalingPlotResult(
            success=False,
            output_path=str(output_path),
            message=f"Error generating plot: {str(e)}",
        )


def build_parser() -> argparse.ArgumentParser:
    """Build argument parser for scaling plot generation."""
    parser = argparse.ArgumentParser(
        description="Generate scaling plot with power-law fits and reliability note."
    )
    parser.add_argument(
        "--input",
        type=Path,
        required=True,
        help="Path to input CSV with scaling data.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Path to output PDF.",
    )
    parser.add_argument(
        "--note",
        type=str,
        default="Note: 3 data points limit power-law reliability.",
        help="Custom note text about data limitations.",
    )
    return parser


def main() -> int:
    """Main entry point for scaling plot generation."""
    parser = build_parser()
    args = parser.parse_args()

    result = generate_scaling_plot_with_notes(
        input_path=args.input,
        output_path=args.output,
        note_text=args.note,
    )

    print(result.message)
    return 0 if result.success else 1


if __name__ == "__main__":
    sys.exit(main())
