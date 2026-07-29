"""
Scaling Plot Generator for User Story 3.

Generates `scaling_plot.pdf` with fitted power-law curves for specialization
index and retrieval efficiency, including an explicit text note stating that
"3 data points limit power-law reliability".

This script reads the scaling results (produced by T027/T028/T029), fits
power-law models, and renders the final publication-quality figure.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import warnings
from pathlib import Path
from typing import Any, Dict, List, Tuple, Optional

import matplotlib
# Use non-interactive backend for CI/headless environments
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats

# Project-relative imports
# We assume this file runs from the project root or code/ directory.
# Adjust sys.path if necessary to find 'analysis' package.
try:
    from analysis.scaling import load_scaling_data, fit_power_law, PowerLawFitResult
    from analysis.scaling_ci import load_scaling_results_for_bootstrap
except ImportError:
    # Fallback for direct execution in code/ directory
    sys.path.insert(0, str(Path(__file__).parent))
    from analysis.scaling import load_scaling_data, fit_power_law, PowerLawFitResult
    from analysis.scaling_ci import load_scaling_results_for_bootstrap


def generate_scaling_plot_with_notes(
    input_data_path: Path,
    output_path: Path,
    agent_counts: Optional[List[int]] = None,
    note_text: str = "3 data points limit power-law reliability"
) -> Dict[str, Any]:
    """
    Generate the scaling plot with fitted power-law curves and a limitation note.

    Args:
        input_data_path: Path to the JSON file containing scaling analysis results
                         (specialization and retrieval metrics by agent count).
        output_path: Path where the PDF plot will be saved.
        agent_counts: Optional list of agent counts to filter/plot. If None, uses all available.
        note_text: The explicit text note to include on the plot.

    Returns:
        A dictionary containing the plot metadata and fit parameters.
    """
    # Load data
    data = load_scaling_data(input_data_path)
    if not data:
        raise ValueError(f"No scaling data found at {input_data_path}")

    # Extract agent counts and metrics
    # Expected data structure: list of dicts with 'agent_count', 'specialization_index', 'retrieval_efficiency'
    agent_counts_list = []
    spec_indices = []
    ret_effs = []

    for row in data:
        n = int(row['agent_count'])
        if agent_counts is None or n in agent_counts:
            agent_counts_list.append(n)
            spec_indices.append(float(row['specialization_index']))
            ret_effs.append(float(row['retrieval_efficiency']))

    if len(agent_counts_list) < 2:
        raise ValueError("Insufficient data points for plotting (need at least 2).")

    agent_counts_list = np.array(agent_counts_list)
    spec_indices = np.array(spec_indices)
    ret_effs = np.array(ret_effs)

    # Sort by agent count for consistent plotting
    sort_idx = np.argsort(agent_counts_list)
    agent_counts_list = agent_counts_list[sort_idx]
    spec_indices = spec_indices[sort_idx]
    ret_effs = ret_effs[sort_idx]

    # Fit power laws
    # y = a * x^b  =>  log(y) = log(a) + b * log(x)
    log_x = np.log(agent_counts_list)

    fit_spec = fit_power_law(log_x, np.log(spec_indices))
    fit_ret = fit_power_law(log_x, np.log(ret_effs))

    # Prepare plot
    fig, ax = plt.subplots(figsize=(10, 7))

    # Plot raw data points
    ax.scatter(agent_counts_list, spec_indices, color='blue', label='Specialization Index', zorder=5, s=80, edgecolors='black')
    ax.scatter(agent_counts_list, ret_effs, color='red', label='Retrieval Efficiency', zorder=5, s=80, marker='s', edgecolors='black')

    # Plot fitted curves
    x_fit = np.linspace(min(agent_counts_list), max(agent_counts_list), 100)
    y_fit_spec = np.exp(fit_spec.intercept) * np.exp(fit_spec.slope * np.log(x_fit))
    y_fit_ret = np.exp(fit_ret.intercept) * np.exp(fit_ret.slope * np.log(x_fit))

    ax.plot(x_fit, y_fit_spec, color='blue', linestyle='--', linewidth=2, alpha=0.8, label=f'Spec Fit (b={fit_spec.slope:.3f})')
    ax.plot(x_fit, y_fit_ret, color='red', linestyle='--', linewidth=2, alpha=0.8, label=f'Ret Fit (b={fit_ret.slope:.3f})')

    # Labels and Title
    ax.set_xlabel('Number of Agents (N)', fontsize=12)
    ax.set_ylabel('Metric Value', fontsize=12)
    ax.set_title('Scaling of Collective Memory Metrics (Power-Law Fit)', fontsize=14)
    ax.legend(fontsize=10)
    ax.grid(True, linestyle=':', alpha=0.6)

    # Add the explicit limitation note as text on the plot
    # Position in the bottom right or top right depending on data density
    # Using figure coordinates for consistent placement
    props = dict(boxstyle='round', facecolor='wheat', alpha=0.8)
    note_position = (0.02, 0.02) # Bottom left
    ax.text(0.5, 0.02, note_text,
            transform=ax.transAxes,
            fontsize=10,
            verticalalignment='bottom',
            horizontalalignment='center',
            bbox=props)

    # Save figure
    plt.tight_layout()
    plt.savefig(output_path, format='pdf', dpi=300)
    plt.close(fig)

    # Return metadata
    return {
        "output_file": str(output_path),
        "agent_counts": agent_counts_list.tolist(),
        "specialization_fit": {
            "exponent": float(fit_spec.slope),
            "intercept": float(fit_spec.intercept),
            "r_squared": float(fit_spec.r_squared)
        },
        "retrieval_fit": {
            "exponent": float(fit_ret.slope),
            "intercept": float(fit_ret.intercept),
            "r_squared": float(fit_ret.r_squared)
        },
        "note": note_text,
        "data_points": len(agent_counts_list)
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate scaling plot with power-law fits and limitation notes."
    )
    parser.add_argument(
        "--input",
        type=str,
        default="data/scaling_results.json",
        help="Path to the input JSON file with scaling analysis results."
    )
    parser.add_argument(
        "--output",
        type=str,
        default="results/scaling_plot.pdf",
        help="Path to save the output PDF plot."
    )
    parser.add_argument(
        "--agents",
        type=str,
        default=None,
        help="Comma-separated list of agent counts to include (e.g., 3,5,7). If None, uses all."
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    agent_counts = None
    if args.agents:
        agent_counts = [int(x.strip()) for x in args.agents.split(',')]

    note = "3 data points limit power-law reliability"

    try:
        result = generate_scaling_plot_with_notes(
            input_data_path=input_path,
            output_path=output_path,
            agent_counts=agent_counts,
            note_text=note
        )
        print(f"Successfully generated plot: {output_path}")
        print(f"Data points used: {result['data_points']}")
        print(f"Specialization exponent: {result['specialization_fit']['exponent']:.4f}")
        print(f"Retrieval exponent: {result['retrieval_fit']['exponent']:.4f}")
    except Exception as e:
        print(f"Error generating plot: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
