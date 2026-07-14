"""Scaling plot generation with power-law fitting and reliability notes.

This module generates the scaling_plot.pdf required for T030, plotting
specialization index and retrieval efficiency against agent count with
fitted power-law curves and an explicit note about the limited data points.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np

# Import from existing project modules
from analysis.scaling import load_scaling_data, aggregate_by_agent_count, fit_power_law
from utils.logging import get_logger


def generate_scaling_plot_with_notes(
    results_path: str,
    output_path: str,
    min_agents: int = 3,
    max_agents: int = 10,
) -> Dict[str, Any]:
    """Generate scaling plot with power-law fits and reliability note.

    Args:
        results_path: Path to the scaling results JSON file.
        output_path: Path where the PDF plot will be saved.
        min_agents: Minimum agent count to include in the plot.
        max_agents: Maximum agent count to include in the plot.

    Returns:
        Dictionary with plot metadata and fit statistics.
    """
    logger = get_logger(__name__)
    logger.log("generate_scaling_plot_with_notes", input_path=results_path, output_path=output_path)

    # Load and aggregate data
    data = load_scaling_data(results_path)
    aggregated = aggregate_by_agent_count(data, min_agents=min_agents, max_agents=max_agents)

    if len(aggregated) < 3:
        logger.log("warning", message="Fewer than 3 data points available for power-law fitting")
        warnings.warn("Fewer than 3 data points for reliable power-law fitting")

    agent_counts = sorted(aggregated.keys())
    spec_indices = [aggregated[n]["specialization_index"] for n in agent_counts]
    retrieval_effs = [aggregated[n]["retrieval_efficiency"] for n in agent_counts]

    # Fit power-law curves
    spec_fit = fit_power_law(agent_counts, spec_indices)
    retrieval_fit = fit_power_law(agent_counts, retrieval_effs)

    # Create the plot
    fig, ax = plt.subplots(figsize=(10, 6))

    # Plot raw data points
    ax.scatter(agent_counts, spec_indices, color='blue', label='Specialization Index', alpha=0.7, s=60)
    ax.scatter(agent_counts, retrieval_effs, color='red', label='Retrieval Efficiency', alpha=0.7, s=60)

    # Generate smooth curve for fits
    x_smooth = np.linspace(min(agent_counts), max(agent_counts), 100)

    if spec_fit["success"]:
        y_spec_smooth = spec_fit["a"] * np.power(x_smooth, spec_fit["b"])
        ax.plot(x_smooth, y_spec_smooth, 'b--', linewidth=2, label=f'Spec Fit (exp={spec_fit["b"]:.3f})')

    if retrieval_fit["success"]:
        y_retrieval_smooth = retrieval_fit["a"] * np.power(x_smooth, retrieval_fit["b"])
        ax.plot(x_smooth, y_retrieval_smooth, 'r--', linewidth=2, label=f'Retrieval Fit (exp={retrieval_fit["b"]:.3f})')

    # Labels and legend
    ax.set_xlabel('Number of Agents', fontsize=12)
    ax.set_ylabel('Metric Value', fontsize=12)
    ax.set_title('Scaling of Collective Memory Metrics with Agent Count', fontsize=14)
    ax.legend(loc='best')
    ax.grid(True, alpha=0.3)

    # Add explicit note about limited data points
    note_text = "Note: 3 data points limit power-law reliability"
    ax.text(0.02, 0.02, note_text, transform=ax.transAxes,
            fontsize=10, verticalalignment='bottom',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    # Save the plot
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()

    logger.log("plot_saved", path=output_path, data_points=len(agent_counts))

    return {
        "output_path": output_path,
        "data_points": len(agent_counts),
        "agent_counts": agent_counts,
        "specialization_fit": spec_fit,
        "retrieval_fit": retrieval_fit,
        "note": note_text
    }


def build_parser() -> argparse.ArgumentParser:
    """Build argument parser for the scaling plot generator."""
    parser = argparse.ArgumentParser(
        description="Generate scaling plot with power-law fits and reliability notes"
    )
    parser.add_argument(
        "--results",
        type=str,
        default="projects/PROJ-586-social-memory-networks-modeling-collecti/results/scaling_results.json",
        help="Path to the scaling results JSON file"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="projects/PROJ-586-social-memory-networks-modeling-collecti/results/scaling_plot.pdf",
        help="Path for the output PDF plot"
    )
    parser.add_argument(
        "--min-agents",
        type=int,
        default=3,
        help="Minimum agent count to include"
    )
    parser.add_argument(
        "--max-agents",
        type=int,
        default=10,
        help="Maximum agent count to include"
    )
    return parser


def main() -> int:
    """Main entry point for the scaling plot generator."""
    parser = build_parser()
    args = parser.parse_args()

    output_dir = Path(args.output).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        result = generate_scaling_plot_with_notes(
            results_path=args.results,
            output_path=args.output,
            min_agents=args.min_agents,
            max_agents=args.max_agents
        )

        print(f"Plot generated successfully: {args.output}")
        print(f"Data points used: {result['data_points']}")
        print(f"Specialization exponent: {result['specialization_fit']['b']:.4f}")
        print(f"Retrieval exponent: {result['retrieval_fit']['b']:.4f}")

        return 0

    except FileNotFoundError as e:
        print(f"Error: Results file not found: {e}")
        return 1
    except Exception as e:
        print(f"Error generating plot: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())