"""Scaling plot generator for User Story 3.

Generates a PDF plot of specialization index and retrieval efficiency versus
number of agents, with fitted power-law curves and an explicit text note about
the limitation of having only 3 data points.
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

# Import project modules
from analysis.scaling import fit_power_law, load_scaling_data


def load_scaling_results_for_plot(results_path: Path) -> List[Dict[str, Any]]:
    """Load scaling analysis results from a JSON file.

    Args:
        results_path: Path to the JSON file containing scaling results.

    Returns:
        List of dictionaries with keys: 'agent_count', 'specialization_index',
        'retrieval_efficiency', and optionally 'ci_lower', 'ci_upper'.
    """
    if not results_path.exists():
        raise FileNotFoundError(f"Scaling results file not found: {results_path}")

    with open(results_path, 'r') as f:
        data = json.load(f)

    # Handle both list and dict formats
    if isinstance(data, dict) and 'results' in data:
        return data['results']
    elif isinstance(data, list):
        return data
    else:
        raise ValueError(f"Unexpected data format in {results_path}")


def generate_scaling_plot_with_notes(
    results: List[Dict[str, Any]],
    output_path: Path,
    title: str = "Scaling of Collective Remembering Metrics",
    note_text: str = "3 data points limit power-law reliability"
) -> None:
    """Generate a PDF plot of scaling metrics with power-law fits and a limitation note.

    Args:
        results: List of scaling result dictionaries.
        output_path: Path to save the PDF plot.
        title: Plot title.
        note_text: Text note to display on the plot about data point limitation.
    """
    if len(results) < 2:
        raise ValueError("At least 2 data points are required for plotting.")

    # Extract data
    agent_counts = sorted([r['agent_count'] for r in results])
    spec_indices = [r['specialization_index'] for r in results if r['agent_count'] in agent_counts]
    ret_effs = [r['retrieval_efficiency'] for r in results if r['agent_count'] in agent_counts]

    # Ensure alignment
    pairs = sorted(zip(agent_counts, spec_indices, ret_effs), key=lambda x: x[0])
    agent_counts = [p[0] for p in pairs]
    spec_indices = [p[1] for p in pairs]
    ret_effs = [p[2] for p in pairs]

    # Convert to numpy arrays
    x = np.array(agent_counts, dtype=float)
    y_spec = np.array(spec_indices, dtype=float)
    y_ret = np.array(ret_effs, dtype=float)

    # Fit power laws
    # y = a * x^b  ->  log(y) = log(a) + b * log(x)
    # Filter out zero/negative values for log transformation
    valid_mask_spec = (y_spec > 0) & (x > 0)
    valid_mask_ret = (y_ret > 0) & (x > 0)

    if np.sum(valid_mask_spec) < 2 or np.sum(valid_mask_ret) < 2:
        warnings.warn("Insufficient valid data points for power-law fitting. "
                     "Plotting raw data without fits.")
        fit_spec = None
        fit_ret = None
    else:
        x_valid_spec = x[valid_mask_spec]
        y_valid_spec = y_spec[valid_mask_spec]
        x_valid_ret = x[valid_mask_ret]
        y_valid_ret = y_ret[valid_mask_ret]

        fit_spec = fit_power_law(x_valid_spec, y_valid_spec)
        fit_ret = fit_power_law(x_valid_ret, y_valid_ret)

    # Create the plot
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    # Plot 1: Specialization Index
    ax1.scatter(x, y_spec, color='blue', s=100, zorder=5, label='Measured')
    if fit_spec:
        x_fit = np.linspace(min(x), max(x), 100)
        y_fit = fit_spec['a'] * np.power(x_fit, fit_spec['b'])
        ax1.plot(x_fit, y_fit, 'b-', linewidth=2, label=f'Power-law fit (β={fit_spec["b"]:.3f})')
    ax1.set_xlabel('Number of Agents')
    ax1.set_ylabel('Specialization Index')
    ax1.set_title('Specialization Index vs. Agent Count')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    ax1.set_xscale('log')
    ax1.set_yscale('log')

    # Plot 2: Retrieval Efficiency
    ax2.scatter(x, y_ret, color='green', s=100, zorder=5, label='Measured')
    if fit_ret:
        x_fit = np.linspace(min(x), max(x), 100)
        y_fit = fit_ret['a'] * np.power(x_fit, fit_ret['b'])
        ax2.plot(x_fit, y_fit, 'g-', linewidth=2, label=f'Power-law fit (β={fit_ret["b"]:.3f})')
    ax2.set_xlabel('Number of Agents')
    ax2.set_ylabel('Retrieval Efficiency')
    ax2.set_title('Retrieval Efficiency vs. Agent Count')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    ax2.set_xscale('log')
    ax2.set_yscale('log')

    # Add the limitation note to both subplots
    note_props = dict(boxstyle='round,pad=0.5', facecolor='yellow', alpha=0.7)
    for ax in [ax1, ax2]:
        ax.text(0.02, 0.98, note_text, transform=ax.transAxes, fontsize=10,
               verticalalignment='top', bbox=note_props)

    # Main title
    fig.suptitle(title, fontsize=16, fontweight='bold')

    # Adjust layout to prevent overlap
    plt.tight_layout(rect=[0, 0, 1, 0.95])

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Save the plot
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close(fig)

    print(f"Scaling plot saved to: {output_path}")


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser for the scaling plot generator."""
    parser = argparse.ArgumentParser(
        description="Generate scaling plot with power-law fits and limitation notes."
    )
    parser.add_argument(
        "--results",
        type=str,
        default="projects/PROJ-586-social-memory-networks-modeling-collecti/results/scaling_results.json",
        help="Path to the scaling results JSON file."
    )
    parser.add_argument(
        "--output",
        type=str,
        default="projects/PROJ-586-social-memory-networks-modeling-collecti/results/scaling_plot.pdf",
        help="Path to save the output PDF plot."
    )
    parser.add_argument(
        "--title",
        type=str,
        default="Scaling of Collective Remembering Metrics",
        help="Plot title."
    )
    parser.add_argument(
        "--note",
        type=str,
        default="3 data points limit power-law reliability",
        help="Text note to display on the plot."
    )
    return parser


def main() -> None:
    """Main entry point for the scaling plot generator."""
    parser = build_parser()
    args = parser.parse_args()

    results_path = Path(args.results)
    output_path = Path(args.output)

    try:
        results = load_scaling_results_for_plot(results_path)
        generate_scaling_plot_with_notes(
            results=results,
            output_path=output_path,
            title=args.title,
            note_text=args.note
        )
    except Exception as e:
        print(f"Error generating scaling plot: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
