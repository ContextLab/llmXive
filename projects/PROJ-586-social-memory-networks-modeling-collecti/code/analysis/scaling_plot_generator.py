"""Scaling plot generator for User Story 3.

Generates `scaling_plot.pdf` with fitted power-law curves and an explicit note
that 3 data points limit power-law reliability.

Reads scaling data from `data/scaling_results.csv` (produced by run_scaling_experiment.py
or run_experiment.py with --plot scaling) and writes the PDF to
`projects/PROJ-586-social-memory-networks-modeling-collecti/results/scaling_plot.pdf`.
"""
from __future__ import annotations

import argparse
import math
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

# Import from existing project modules
from analysis.scaling import fit_power_law, load_scaling_data

try:
    import matplotlib
    matplotlib.use("Agg")  # Non-interactive backend for headless execution
    import matplotlib.pyplot as plt
except ImportError:
    print("ERROR: matplotlib is required. Install with: pip install matplotlib", file=sys.stderr)
    sys.exit(1)

try:
    from scipy.optimize import curve_fit
except ImportError:
    print("ERROR: scipy is required. Install with: pip install scipy", file=sys.stderr)
    sys.exit(1)

@dataclass
class ScalingPlotResult:
    """Result of generating the scaling plot."""
    pdf_path: Path
    fitted_exponent: float | None
    n_points: int
    note_included: bool


def power_law(x: np.ndarray, a: float, b: float) -> np.ndarray:
    """Power law function: y = a * x^b."""
    return a * np.power(x, b)


def load_scaling_data_real(input_path: Path | str) -> pd.DataFrame:
    """Load scaling data from CSV.

    Expects columns: agent_count, specialization_index, retrieval_efficiency
    (or aggregated equivalents).
    """
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Scaling data not found: {path}")

    df = pd.read_csv(path)

    # Ensure required columns exist
    required = ["agent_count", "specialization_index", "retrieval_efficiency"]
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in {path}: {missing}")

    # Filter out invalid rows
    df = df.dropna(subset=required)
    df = df[df["agent_count"] > 0]

    return df


def fit_power_law_with_ci(
    x: np.ndarray,
    y: np.ndarray,
    confidence: float = 0.95
) -> tuple[float, float, tuple[float, float], tuple[float, float]]:
    """Fit power law y = a * x^b with confidence intervals.

    Returns:
        (a, b, (a_low, a_high), (b_low, b_high))
    """
    if len(x) < 2:
        raise ValueError("Need at least 2 points to fit a power law")

    # Log-transform for linear fitting: log(y) = log(a) + b * log(x)
    log_x = np.log(x)
    log_y = np.log(y)

    # Fit linear model
    coeffs = np.polyfit(log_x, log_y, 1)
    b = coeffs[0]
    log_a = coeffs[1]
    a = np.exp(log_a)

    # Estimate confidence intervals using residual variance
    y_pred = np.exp(log_a + b * log_x)
    residuals = log_y - (log_a + b * log_x)
    s_err = np.sqrt(np.sum(residuals**2) / (len(x) - 2))

    # Covariance matrix for coefficients
    cov = np.cov(log_x, log_y)
    # Use polyfit's covariance if available, else approximate
    try:
        popt, pcov = curve_fit(power_law, x, y, p0=[1.0, 1.0])
        perr = np.sqrt(np.diag(pcov))
        a_err, b_err = perr
    except Exception:
        # Fallback: approximate error from log-linear fit
        n = len(x)
        t_val = 2.0 if n >= 3 else 4.303  # Approximate t for 95% CI
        a_err = abs(a) * s_err * t_val / np.sqrt(n)
        b_err = s_err * t_val / np.sqrt(np.sum((log_x - np.mean(log_x))**2))

    a_low, a_high = a - a_err, a + a_err
    b_low, b_high = b - b_err, b + b_err

    return a, b, (a_low, a_high), (b_low, b_high)


def generate_scaling_plot_with_notes(
    input_path: Path | str,
    output_path: Path | str,
    figsize: tuple[float, float] = (10, 8)
) -> ScalingPlotResult:
    """Generate scaling plot with power-law fit and reliability note.

    Args:
        input_path: Path to scaling data CSV
        output_path: Path for output PDF
        figsize: Figure size in inches

    Returns:
        ScalingPlotResult with metadata
    """
    df = load_scaling_data_real(input_path)

    # Aggregate by agent_count if multiple runs exist
    agg = df.groupby("agent_count").agg({
        "specialization_index": "mean",
        "retrieval_efficiency": "mean"
    }).reset_index()

    agent_counts = agg["agent_count"].values
    spec_indices = agg["specialization_index"].values
    ret_effs = agg["retrieval_efficiency"].values

    n_points = len(agent_counts)

    # Create figure
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)

    # Plot specialization index
    ax1.errorbar(
        agent_counts, spec_indices,
        yerr=np.std(spec_indices) if len(spec_indices) > 1 else 0,
        fmt='o-', capsize=5, label='Specialization Index', color='blue'
    )

    # Fit power law for specialization
    fitted_exp_spec = None
    if n_points >= 2:
        try:
            a, b, _, _ = fit_power_law_with_ci(agent_counts, spec_indices)
            fitted_exp_spec = b
            x_fit = np.linspace(min(agent_counts), max(agent_counts), 100)
            y_fit = a * np.power(x_fit, b)
            ax1.plot(x_fit, y_fit, 'r--', label=f'Power-law fit (β={b:.3f})')
        except Exception as e:
            ax1.text(0.5, 0.5, f'Fit failed: {e}', transform=ax1.transAxes,
                    ha='center', va='center', alpha=0.7)

    ax1.set_xlabel('Number of Agents')
    ax1.set_ylabel('Specialization Index')
    ax1.set_title('Specialization vs Agent Count')
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # Plot retrieval efficiency
    ax2.errorbar(
        agent_counts, ret_effs,
        yerr=np.std(ret_effs) if len(ret_effs) > 1 else 0,
        fmt='s-', capsize=5, label='Retrieval Efficiency', color='green'
    )

    # Fit power law for retrieval
    fitted_exp_ret = None
    if n_points >= 2:
        try:
            a, b, _, _ = fit_power_law_with_ci(agent_counts, ret_effs)
            fitted_exp_ret = b
            x_fit = np.linspace(min(agent_counts), max(agent_counts), 100)
            y_fit = a * np.power(x_fit, b)
            ax2.plot(x_fit, y_fit, 'r--', label=f'Power-law fit (β={b:.3f})')
        except Exception as e:
            ax2.text(0.5, 0.5, f'Fit failed: {e}', transform=ax2.transAxes,
                    ha='center', va='center', alpha=0.7)

    ax2.set_xlabel('Number of Agents')
    ax2.set_ylabel('Retrieval Efficiency')
    ax2.set_title('Retrieval Efficiency vs Agent Count')
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    # Add explicit note about 3 data points limitation
    note_text = (
        "NOTE: Power-law reliability limited.\n"
        "Only 3 data points (agent counts 3, 5, 7) available.\n"
        "Fitted exponents should be interpreted with caution."
    )
    fig.text(
        0.5, 0.02, note_text,
        ha='center', va='bottom', fontsize=10,
        bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.5)
    )

    plt.tight_layout(rect=[0, 0.08, 1, 1])  # Make room for note

    # Ensure output directory exists
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Save PDF
    fig.savefig(output_path, format='pdf', dpi=150)
    plt.close(fig)

    # Determine representative exponent (average of both if both fitted)
    final_exp = None
    if fitted_exp_spec is not None and fitted_exp_ret is not None:
        final_exp = (fitted_exp_spec + fitted_exp_ret) / 2
    elif fitted_exp_spec is not None:
        final_exp = fitted_exp_spec
    elif fitted_exp_ret is not None:
        final_exp = fitted_exp_ret

    return ScalingPlotResult(
        pdf_path=output_path,
        fitted_exponent=final_exp,
        n_points=n_points,
        note_included=True
    )


def build_parser() -> argparse.ArgumentParser:
    """Build argument parser for the scaling plot generator."""
    parser = argparse.ArgumentParser(
        description="Generate scaling plot with power-law fit and reliability note."
    )
    parser.add_argument(
        "--input", "-i",
        type=Path,
        default="data/scaling_results.csv",
        help="Path to scaling data CSV (default: data/scaling_results.csv)"
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default="projects/PROJ-586-social-memory-networks-modeling-collecti/results/scaling_plot.pdf",
        help="Path for output PDF (default: projects/.../results/scaling_plot.pdf)"
    )
    return parser


def main() -> int:
    """Main entry point."""
    parser = build_parser()
    args = parser.parse_args()

    try:
        result = generate_scaling_plot_with_notes(args.input, args.output)
        print(f"Generated: {result.pdf_path}")
        print(f"  Data points: {result.n_points}")
        print(f"  Note included: {result.note_included}")
        if result.fitted_exponent is not None:
            print(f"  Fitted exponent: {result.fitted_exponent:.4f}")
        else:
            print("  Fitted exponent: Could not compute (insufficient data)")
        return 0
    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"ERROR: Unexpected error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())