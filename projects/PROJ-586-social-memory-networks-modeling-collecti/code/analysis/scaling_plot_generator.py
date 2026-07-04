"""
Scaling Plot Generator for User Story 3.

Generates `scaling_plot.pdf` with fitted power-law curves and an explicit
note that 3 data points limit power-law reliability.

This module loads real scaling data (computed by run_experiment.py or
generate_scaling_data.py), fits a power-law model, and produces a PDF
plot with confidence intervals and the required reliability disclaimer.
"""
from __future__ import annotations

import argparse
import math
import sys
import warnings
from pathlib import Path
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

# Try to import matplotlib; if missing, we can't generate the plot.
try:
    import matplotlib
    matplotlib.use("Agg")  # Non-interactive backend for headless environments
    import matplotlib.pyplot as plt
except ImportError:
    plt = None  # type: ignore

# Import the real data loader from the project's analysis module.
# The function load_scaling_data_real is expected to exist in code/analysis/scaling_plot.py
# or code/analysis/scaling.py. We import from scaling_plot.py as per the API surface.
try:
    from analysis.scaling_plot import load_scaling_data_real
except ImportError:
    # Fallback: try loading from scaling.py if the function is there.
    try:
        from analysis.scaling import load_scaling_data as load_scaling_data_real
    except ImportError:
        raise ImportError(
            "Could not import load_scaling_data_real from analysis.scaling_plot "
            "or load_scaling_data from analysis.scaling. Ensure the data loader exists."
        )


@dataclass
class ScalingPlotResult:
    """Result of the scaling plot generation."""
    plot_path: Path
    fit_params: Dict[str, float]
    r_squared: float
    notes: List[str]


def power_law(x: np.ndarray, a: float, b: float) -> np.ndarray:
    """Compute y = a * x^b."""
    return a * np.power(x, b)


def fit_power_law(
    x: np.ndarray, y: np.ndarray
) -> Tuple[float, float, float]:
    """
    Fit a power-law model y = a * x^b by linearizing via log-log transform.

    Returns:
        (a, b, r_squared): Fitted parameters and R-squared of the fit.
    """
    if len(x) < 2:
        raise ValueError("Need at least 2 points to fit a power law.")

    # Log-transform
    log_x = np.log(x)
    log_y = np.log(y)

    # Linear regression: log_y = log_a + b * log_x
    # Use numpy's polyfit for simplicity
    coeffs = np.polyfit(log_x, log_y, 1)
    b = coeffs[0]
    log_a = coeffs[1]
    a = math.exp(log_a)

    # Compute R-squared
    y_pred = a * np.power(x, b)
    ss_res = np.sum((y - y_pred) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0.0

    return a, b, r_squared


def fit_power_law_with_ci(
    x: np.ndarray, y: np.ndarray, confidence: float = 0.95
) -> Tuple[float, float, float, np.ndarray, np.ndarray]:
    """
    Fit power law and compute confidence intervals for the fitted curve.

    Returns:
        (a, b, r_squared, y_lower, y_upper): Fitted params and CI bounds.
    """
    a, b, r_squared = fit_power_law(x, y)

    # For simplicity, we compute CI on the log-scale and transform back.
    # This is an approximation but sufficient for visualization.
    log_x = np.log(x)
    log_y = np.log(y)

    # Linear regression residuals
    log_y_pred = np.polyval([b, math.log(a)], log_x)
    residuals = log_y - log_y_pred
    std_err = np.std(residuals, ddof=2)  # ddof=2 for 2 parameters

    # t-value for confidence interval (approximate with normal for large N, but N=3 here)
    # For N=3, df=1, t_{0.975,1} = 12.706. We'll use a conservative value.
    from scipy import stats
    n = len(x)
    if n > 2:
        t_val = stats.t.ppf((1 + confidence) / 2, df=n - 2)
    else:
        t_val = 12.706  # Conservative for N=3

    margin = t_val * std_err

    # Upper and lower bounds on log-scale
    log_y_upper = log_y_pred + margin
    log_y_lower = log_y_pred - margin

    y_upper = np.exp(log_y_upper)
    y_lower = np.exp(log_y_lower)

    return a, b, r_squared, y_lower, y_upper


def generate_scaling_plot_with_notes(
    data_path: Path,
    output_path: Path,
    metric: str = "specialization_index",
    confidence: float = 0.95,
) -> ScalingPlotResult:
    """
    Generate a PDF plot of metric vs. agent count with power-law fit and notes.

    Args:
        data_path: Path to the scaling data CSV.
        output_path: Path to save the PDF plot.
        metric: Which metric to plot (e.g., 'specialization_index', 'retrieval_efficiency').
        confidence: Confidence level for the error bands.

    Returns:
        ScalingPlotResult with plot path and fit details.
    """
    if plt is None:
        raise RuntimeError("matplotlib is required to generate the plot.")

    # Load data
    df = load_scaling_data_real(data_path)

    # Ensure required columns
    required_cols = ["agent_count", metric]
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required column '{col}' in {data_path}")

    # Sort by agent_count
    df = df.sort_values("agent_count")

    x = df["agent_count"].values.astype(float)
    y = df[metric].values.astype(float)

    # Fit power law
    try:
        a, b, r_squared, y_lower, y_upper = fit_power_law_with_ci(x, y, confidence)
    except Exception as e:
        raise RuntimeError(f"Failed to fit power law: {e}") from e

    # Create plot
    fig, ax = plt.subplots(figsize=(10, 6))

    # Plot data points
    ax.scatter(x, y, color="blue", s=100, zorder=5, label="Observed Data")

    # Plot fitted curve
    x_fit = np.linspace(min(x), max(x), 100)
    y_fit = power_law(x_fit, a, b)
    ax.plot(x_fit, y_fit, color="red", linestyle="--", linewidth=2, label=f"Power-law fit (R²={r_squared:.3f})")

    # Plot confidence band
    # We need to recompute y_lower and y_upper for the fit range
    log_x_fit = np.log(x_fit)
    log_y_fit = np.log(y_fit)
    # Residuals from the fit (on log scale)
    log_y_obs = np.log(y)
    log_y_pred_fit = np.polyval([b, math.log(a)], np.log(x))
    residuals = log_y_obs - log_y_pred_fit
    std_err = np.std(residuals, ddof=2)
    from scipy import stats
    n = len(x)
    if n > 2:
        t_val = stats.t.ppf((1 + confidence) / 2, df=n - 2)
    else:
        t_val = 12.706
    margin = t_val * std_err

    y_upper_fit = y_fit * np.exp(margin)
    y_lower_fit = y_fit * np.exp(-margin)

    ax.fill_between(x_fit, y_lower_fit, y_upper_fit, color="red", alpha=0.2, label=f"{confidence*100:.0f}% CI")

    # Add explicit note about 3 data points limiting reliability
    note_text = (
        "Note: Only 3 data points (agent counts 3, 5, 7) are available. "
        "Power-law fitting with N=3 has limited statistical reliability. "
        "The fitted exponent should be interpreted as a preliminary estimate."
    )

    # Add text box to plot
    props = dict(boxstyle='round', facecolor='wheat', alpha=0.8)
    ax.text(
        0.02, 0.98, note_text,
        transform=ax.transAxes, fontsize=10,
        verticalalignment='top', bbox=props,
        wrap=True
    )

    ax.set_xlabel("Number of Agents", fontsize=12)
    ax.set_ylabel(metric.replace("_", " ").title(), fontsize=12)
    ax.set_title(f"Scaling of {metric.replace('_', ' ').title()} vs. Agent Count", fontsize=14)
    ax.legend()
    ax.grid(True, linestyle='--', alpha=0.5)

    # Save to PDF
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(output_path, format="pdf")
    plt.close(fig)

    return ScalingPlotResult(
        plot_path=output_path,
        fit_params={"a": a, "b": b, "r_squared": r_squared},
        r_squared=r_squared,
        notes=[note_text]
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate scaling plot with power-law fit and reliability note."
    )
    parser.add_argument(
        "--input", "-i",
        type=Path,
        required=True,
        help="Path to the scaling data CSV (e.g., data/scaling_results.csv)"
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        required=True,
        help="Path to save the PDF plot (e.g., results/scaling_plot.pdf)"
    )
    parser.add_argument(
        "--metric", "-m",
        type=str,
        default="specialization_index",
        choices=["specialization_index", "retrieval_efficiency"],
        help="Which metric to plot"
    )
    parser.add_argument(
        "--confidence", "-c",
        type=float,
        default=0.95,
        help="Confidence level for the error bands"
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if not args.input.exists():
        print(f"Error: Input file not found: {args.input}", file=sys.stderr)
        return 1

    try:
        result = generate_scaling_plot_with_notes(
            data_path=args.input,
            output_path=args.output,
            metric=args.metric,
            confidence=args.confidence,
        )
        print(f"Plot saved to: {result.plot_path}")
        print(f"Power-law fit: y = {result.fit_params['a']:.4f} * x^{result.fit_params['b']:.4f}")
        print(f"R-squared: {result.fit_params['r_squared']:.4f}")
        return 0
    except Exception as e:
        print(f"Error generating plot: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())