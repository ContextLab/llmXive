"""Scaling plot generation for US-3.

Generates a PDF plot of specialization index and retrieval efficiency vs. agent count,
with fitted power-law curves and an explicit note about the limitation of 3 data points.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for CI
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Import from existing project modules
# Note: We assume scaling_ci.py or scaling.py provides the fit results
# If not, we compute them here to ensure the plot is self-contained.
try:
    from analysis.scaling_ci import load_scaling_results_for_bootstrap, bootstrap_power_law_ci
except ImportError:
    # Fallback if scaling_ci is not available or fails
    load_scaling_results_for_bootstrap = None
    bootstrap_power_law_ci = None

from metrics.specialization import compute_specialization_index
from metrics.retrieval import compute_retrieval_efficiency

# Constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
RESULTS_DIR = PROJECT_ROOT / "projects" / "PROJ-586-social-memory-networks-modeling-collecti" / "results"
OUTPUT_PDF = RESULTS_DIR / "scaling_plot.pdf"
DATA_JSON = RESULTS_DIR / "scaling_confidence_intervals.json"

# Ensure output directory exists
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def power_law(x: np.ndarray, a: float, b: float) -> np.ndarray:
    """Power law function: y = a * x^b"""
    return a * np.power(x, b)


def fit_power_law(x: np.ndarray, y: np.ndarray) -> Tuple[float, float]:
    """Fit a power law y = a * x^b to data using log-log linear regression.

    Args:
        x: Independent variable (agent count)
        y: Dependent variable (metric value)

    Returns:
        Tuple of (a, b) coefficients.
    """
    # Filter out non-positive values for log
    mask = (x > 0) & (y > 0)
    x_log = np.log(x[mask])
    y_log = np.log(y[mask])

    if len(x_log) < 2:
        # Not enough points to fit
        return 1.0, 0.0

    # Linear regression on log-log
    coeffs = np.polyfit(x_log, y_log, 1)
    b = coeffs[0]  # exponent
    a = math.exp(coeffs[1])  # coefficient

    return a, b


def load_scaling_results_for_plot(json_path: Optional[Path] = None) -> pd.DataFrame:
    """Load scaling results from the confidence intervals JSON file.

    Args:
        json_path: Path to the JSON file. Defaults to DATA_JSON.

    Returns:
        DataFrame with columns: agent_count, specialization_index, retrieval_efficiency,
        spec_ci_low, spec_ci_high, ret_ci_low, ret_ci_high
    """
    if json_path is None:
        json_path = DATA_JSON

    if not json_path.exists():
        raise FileNotFoundError(f"Scaling results JSON not found: {json_path}. "
                                "Run the scaling analysis first (T029).")

    with open(json_path, 'r') as f:
        data = json.load(f)

    # Convert to DataFrame
    df = pd.DataFrame(data)

    # Ensure numeric types
    numeric_cols = ['agent_count', 'specialization_index', 'retrieval_efficiency',
                    'spec_ci_low', 'spec_ci_high', 'ret_ci_low', 'ret_ci_high']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    return df


def generate_scaling_plot_with_notes(
    df: pd.DataFrame,
    output_path: Optional[Path] = None,
    title: str = "Scaling of Collective Remembering Metrics"
) -> None:
    """Generate the scaling plot with power-law fits and reliability note.

    Args:
        df: DataFrame with scaling results.
        output_path: Path to save the PDF. Defaults to OUTPUT_PDF.
        title: Plot title.
    """
    if output_path is None:
        output_path = OUTPUT_PDF

    # Ensure we have data
    if df.empty:
        raise ValueError("Input DataFrame is empty. Cannot generate plot.")

    # Sort by agent count
    df = df.sort_values('agent_count')

    agent_counts = df['agent_count'].values
    spec_indices = df['specialization_index'].values
    ret_effs = df['retrieval_efficiency'].values

    # Fit power laws
    a_spec, b_spec = fit_power_law(agent_counts, spec_indices)
    a_ret, b_ret = fit_power_law(agent_counts, ret_effs)

    # Generate smooth curves for plotting
    x_smooth = np.linspace(min(agent_counts), max(agent_counts), 100)
    y_spec_smooth = power_law(x_smooth, a_spec, b_spec)
    y_ret_smooth = power_law(x_smooth, a_ret, b_ret)

    # Create the plot
    fig, ax = plt.subplots(figsize=(10, 6))

    # Plot data points with error bars
    ax.errorbar(
        agent_counts,
        spec_indices,
        yerr=[spec_indices - df['spec_ci_low'].values, df['spec_ci_high'].values - spec_indices],
        fmt='o-',
        label='Specialization Index',
        color='blue',
        capsize=5,
        markersize=8,
        linewidth=2
    )

    ax.errorbar(
        agent_counts,
        ret_effs,
        yerr=[ret_effs - df['ret_ci_low'].values, df['ret_ci_high'].values - ret_effs],
        fmt='s-',
        label='Retrieval Efficiency',
        color='red',
        capsize=5,
        markersize=8,
        linewidth=2
    )

    # Plot fitted curves
    ax.plot(x_smooth, y_spec_smooth, 'b--', label=f'Spec Fit: y={a_spec:.2f}x^{b_spec:.2f}', alpha=0.7)
    ax.plot(x_smooth, y_ret_smooth, 'r--', label=f'Ret Fit: y={a_ret:.2f}x^{b_ret:.2f}', alpha=0.7)

    # Labels and title
    ax.set_xlabel('Number of Agents', fontsize=12)
    ax.set_ylabel('Metric Value', fontsize=12)
    ax.set_title(title, fontsize=14)
    ax.legend(loc='best', fontsize=10)
    ax.grid(True, alpha=0.3)

    # Add explicit note about data point limitation
    note_text = "Note: 3 data points limit power-law reliability"
    ax.text(
        0.02, 0.02,
        note_text,
        transform=ax.transAxes,
        fontsize=10,
        verticalalignment='bottom',
        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5)
    )

    # Save the plot
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, format='pdf')
    plt.close()

    print(f"Scaling plot saved to: {output_path}")


def run_scaling_analysis(
    json_path: Optional[Path] = None,
    output_path: Optional[Path] = None
) -> None:
    """Run the full scaling analysis and plot generation.

    Args:
        json_path: Path to the input JSON file.
        output_path: Path to save the PDF plot.
    """
    if json_path is None:
        json_path = DATA_JSON
    if output_path is None:
        output_path = OUTPUT_PDF

    print(f"Loading scaling results from: {json_path}")
    df = load_scaling_results_for_plot(json_path)

    print(f"Generating scaling plot to: {output_path}")
    generate_scaling_plot_with_notes(df, output_path)


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser for the script."""
    parser = argparse.ArgumentParser(
        description='Generate scaling plot for collective remembering metrics.'
    )
    parser.add_argument(
        '--input',
        type=Path,
        default=DATA_JSON,
        help='Path to the input JSON file with scaling results.'
    )
    parser.add_argument(
        '--output',
        type=Path,
        default=OUTPUT_PDF,
        help='Path to save the output PDF plot.'
    )
    return parser


def main() -> int:
    """Main entry point for the script."""
    parser = build_parser()
    args = parser.parse_args()

    try:
        run_scaling_analysis(args.input, args.output)
        return 0
    except Exception as e:
        print(f"Error generating scaling plot: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())