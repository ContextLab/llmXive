"""Scaling plot generation for User Story 3.

Generates a PDF plot of specialization index and retrieval efficiency
versus agent count with fitted power-law curves. Includes a specific
footnote regarding the reliability of power-law fits on small datasets.
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
matplotlib.use('Agg')  # Non-interactive backend for headless execution
import matplotlib.pyplot as plt
import numpy as np

from analysis.scaling import (
    PowerLawFitResult,
    ScalingAnalysisResult,
    aggregate_by_agent_count,
    fit_power_law,
    load_scaling_data,
    run_scaling_analysis,
)
from utils.logging import get_logger

logger = get_logger(__name__)


def load_scaling_results_for_plot(
    input_path: str,
) -> Tuple[List[float], List[float], List[float], List[float], List[int]]:
    """Load aggregated scaling results from CSV.

    Args:
        input_path: Path to the CSV file containing aggregated results.

    Returns:
        Tuple of (agent_counts, spec_means, spec_stds, ret_means, ret_stds).
    """
    data = load_scaling_data(input_path)
    if not data:
        raise FileNotFoundError(f"No data found in {input_path}")

    agent_counts: List[int] = []
    spec_means: List[float] = []
    spec_stds: List[float] = []
    ret_means: List[float] = []
    ret_stds: List[float] = []

    for row in data:
        agent_counts.append(int(row["agent_count"]))
        spec_means.append(float(row["mean_specialization"]))
        spec_stds.append(float(row["std_specialization"]))
        ret_means.append(float(row["mean_retrieval"]))
        ret_stds.append(float(row["std_retrieval"]))

    return agent_counts, spec_means, spec_stds, ret_means, ret_stds


def generate_scaling_plot_with_notes(
    agent_counts: List[int],
    spec_means: List[float],
    spec_stds: List[float],
    ret_means: List[float],
    ret_stds: List[float],
    output_path: str,
    fit_results: Optional[Dict[str, PowerLawFitResult]] = None,
) -> None:
    """Generate the scaling plot with power-law fits and reliability note.

    Args:
        agent_counts: List of agent counts.
        spec_means: Mean specialization index for each count.
        spec_stds: Standard deviation of specialization index.
        ret_means: Mean retrieval efficiency for each count.
        ret_stds: Standard deviation of retrieval efficiency.
        output_path: Path to save the PDF plot.
        fit_results: Optional dict of fit results for annotation.
    """
    if len(agent_counts) < 2:
        raise ValueError("At least two data points are required for plotting.")

    # Convert to numpy arrays for fitting
    x = np.array(agent_counts, dtype=float)
    y_spec = np.array(spec_means, dtype=float)
    y_ret = np.array(ret_means, dtype=float)

    # Create figure
    fig, ax = plt.subplots(figsize=(10, 6))

    # Plot data points with error bars
    ax.errorbar(
        x, y_spec, yerr=spec_stds,
        fmt='o', color='blue', label='Specialization Index', capsize=5, alpha=0.7
    )
    ax.errorbar(
        x, y_ret, yerr=ret_stds,
        fmt='s', color='green', label='Retrieval Efficiency', capsize=5, alpha=0.7
    )

    # Fit and plot power laws if results are provided
    if fit_results:
        if 'specialization' in fit_results and fit_results['specialization']:
            fit = fit_results['specialization']
            if fit.exponent is not None and fit.coefficient is not None:
                # Generate smooth curve for fitting
                x_fit = np.linspace(min(x), max(x), 100)
                y_fit = fit.coefficient * np.power(x_fit, fit.exponent)
                ax.plot(x_fit, y_fit, 'b-', linestyle='--', alpha=0.5,
                        label=f'Spec Fit: y={fit.coefficient:.2f}x^{fit.exponent:.2f}')

        if 'retrieval' in fit_results and fit_results['retrieval']:
            fit = fit_results['retrieval']
            if fit.exponent is not None and fit.coefficient is not None:
                x_fit = np.linspace(min(x), max(x), 100)
                y_fit = fit.coefficient * np.power(x_fit, fit.exponent)
                ax.plot(x_fit, y_fit, 'g-', linestyle='--', alpha=0.5,
                        label=f'Ret Fit: y={fit.coefficient:.2f}x^{fit.exponent:.2f}')

    ax.set_xlabel('Number of Agents (N)', fontsize=12)
    ax.set_ylabel('Metric Value', fontsize=12)
    ax.set_title('Scaling of Collective Remembering Metrics', fontsize=14)
    ax.legend(loc='best')
    ax.grid(True, alpha=0.3)

    # Set x-axis to log scale if we have enough range, otherwise linear
    if max(x) > min(x) * 2:
        ax.set_xscale('log')

    # Add the required reliability note as a footnote
    note_text = (
        "Note: a limited number of data points limits power-law reliability. "
        "Exponents should be interpreted with caution."
    )
    fig.text(
        0.5, -0.05, note_text,
        ha='center', va='center', fontsize=10, style='italic',
        bbox=dict(facecolor='white', alpha=0.8, boxstyle='round,pad=0.5')
    )

    plt.tight_layout()
    plt.savefig(output_path, format='pdf', bbox_inches='tight')
    plt.close(fig)
    logger.info(f"Scaling plot saved to {output_path}")


def run_scaling_analysis(
    input_path: str,
    output_plot_path: str,
) -> None:
    """Run the full scaling analysis and generate the plot.

    Args:
        input_path: Path to the raw scaling data CSV.
        output_plot_path: Path to save the output PDF plot.
    """
    # Load and aggregate data
    data = load_scaling_data(input_path)
    if not data:
        raise FileNotFoundError(f"No data found in {input_path}")

    aggregated = aggregate_by_agent_count(data)

    # Extract lists for plotting
    agent_counts = sorted(aggregated.keys())
    spec_means = [aggregated[n]["mean_specialization"] for n in agent_counts]
    spec_stds = [aggregated[n]["std_specialization"] for n in agent_counts]
    ret_means = [aggregated[n]["mean_retrieval"] for n in agent_counts]
    ret_stds = [aggregated[n]["std_retrieval"] for n in agent_counts]

    # Perform fitting
    fit_results = {}
    try:
        fit_spec = fit_power_law(np.array(agent_counts), np.array(spec_means))
        fit_results['specialization'] = fit_spec
        logger.info(f"Specialization fit: exponent={fit_spec.exponent:.4f}")
    except Exception as e:
        logger.warning(f"Could not fit specialization power law: {e}")
        fit_results['specialization'] = None

    try:
        fit_ret = fit_power_law(np.array(agent_counts), np.array(ret_means))
        fit_results['retrieval'] = fit_ret
        logger.info(f"Retrieval fit: exponent={fit_ret.exponent:.4f}")
    except Exception as e:
        logger.warning(f"Could not fit retrieval power law: {e}")
        fit_results['retrieval'] = None

    # Generate plot
    generate_scaling_plot_with_notes(
        agent_counts,
        spec_means,
        spec_stds,
        ret_means,
        ret_stds,
        output_plot_path,
        fit_results
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate scaling plot.")
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Path to the input CSV with aggregated scaling data."
    )
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Path to save the output PDF plot."
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    # Ensure output directory exists
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    run_scaling_analysis(args.input, str(output_path))


if __name__ == "__main__":
    main()