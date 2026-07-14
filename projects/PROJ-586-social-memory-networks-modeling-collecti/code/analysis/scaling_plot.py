"""Generate scaling plot for specialization and retrieval metrics.

This module generates a PDF plot showing the fitted power-law curves for
specialization index and retrieval efficiency versus agent count, with
an explicit note about the limitation of having only 3 data points.
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
from analysis.scaling import load_scaling_data, fit_power_law_with_ci


def load_scaling_results_for_plot(results_dir: Path) -> Dict[str, Any]:
    """Load scaling results from JSON file.

    Args:
        results_dir: Directory containing the scaling results JSON file.

    Returns:
        Dictionary with scaling results data.

    Raises:
        FileNotFoundError: If the results file does not exist.
        json.JSONDecodeError: If the file contains invalid JSON.
    """
    results_file = results_dir / "scaling_confidence_intervals.json"
    if not results_file.exists():
        raise FileNotFoundError(f"Results file not found: {results_file}")

    with open(results_file, "r") as f:
        return json.load(f)


def generate_scaling_plot_with_notes(
    results: Dict[str, Any],
    output_path: Path,
    note_text: str = "3 data points limit power-law reliability"
) -> None:
    """Generate scaling plot with power-law fits and limitation note.

    Creates a PDF plot showing specialization index and retrieval efficiency
    versus agent count, with fitted power-law curves and a text note about
    the limited number of data points.

    Args:
        results: Dictionary containing scaling results with agent counts,
                 metrics, and confidence intervals.
        output_path: Path to save the generated PDF plot.
        note_text: Text note to display on the plot about data limitations.
    """
    # Extract data from results
    agent_counts = results.get("agent_counts", [])
    specialization_data = results.get("specialization", {})
    retrieval_data = results.get("retrieval", {})

    # Extract mean values and confidence intervals
    spec_means = specialization_data.get("means", [])
    spec_ci_lower = specialization_data.get("ci_lower", [])
    spec_ci_upper = specialization_data.get("ci_upper", [])

    ret_means = retrieval_data.get("means", [])
    ret_ci_lower = retrieval_data.get("ci_lower", [])
    ret_ci_upper = retrieval_data.get("ci_upper", [])

    # Fit power-law curves
    spec_fit = fit_power_law_with_ci(np.array(agent_counts), np.array(spec_means))
    ret_fit = fit_power_law_with_ci(np.array(agent_counts), np.array(ret_means))

    # Create figure with two subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    # Plot specialization index
    ax1.errorbar(
        agent_counts, spec_means,
        yerr=[np.array(spec_means) - np.array(spec_ci_lower),
              np.array(spec_ci_upper) - np.array(spec_means)],
        fmt='o-', capsize=5, label='Specialization Index (measured)',
        color='blue', alpha=0.7
    )

    # Generate smooth curve for power-law fit
    x_smooth = np.linspace(min(agent_counts), max(agent_counts), 100)
    y_spec_smooth = spec_fit['a'] * (x_smooth ** spec_fit['b'])
    ax1.plot(x_smooth, y_spec_smooth, 'r--', label=f'Power-law fit: y={spec_fit["a"]:.3f}x^{spec_fit["b"]:.3f}')

    ax1.set_xlabel('Number of Agents')
    ax1.set_ylabel('Specialization Index')
    ax1.set_title('Specialization Index vs Agent Count')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    ax1.set_xscale('log')
    ax1.set_yscale('log')

    # Plot retrieval efficiency
    ax2.errorbar(
        agent_counts, ret_means,
        yerr=[np.array(ret_means) - np.array(ret_ci_lower),
              np.array(ret_ci_upper) - np.array(ret_means)],
        fmt='o-', capsize=5, label='Retrieval Efficiency (measured)',
        color='green', alpha=0.7
    )

    y_ret_smooth = ret_fit['a'] * (x_smooth ** ret_fit['b'])
    ax2.plot(x_smooth, y_ret_smooth, 'r--', label=f'Power-law fit: y={ret_fit["a"]:.3f}x^{ret_fit["b"]:.3f}')

    ax2.set_xlabel('Number of Agents')
    ax2.set_ylabel('Retrieval Efficiency')
    ax2.set_title('Retrieval Efficiency vs Agent Count')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    ax2.set_xscale('log')
    ax2.set_yscale('log')

    # Add limitation note to both subplots
    fig.suptitle('Scaling Analysis: Collective Remembering in Multi-Agent Systems', fontsize=14, fontweight='bold')

    # Add text note about data limitation
    note = f"Note: {note_text}"
    fig.text(0.5, 0.02, note, ha='center', va='bottom', fontsize=10, style='italic',
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Save as PDF
    plt.tight_layout(rect=[0, 0.05, 1, 0.95])
    plt.savefig(output_path, format='pdf', dpi=150, bbox_inches='tight')
    plt.close()

    print(f"Scaling plot saved to: {output_path}")


def build_parser() -> argparse.ArgumentParser:
    """Build argument parser for scaling plot generation."""
    parser = argparse.ArgumentParser(
        description='Generate scaling plot with power-law fits and limitation notes.'
    )
    parser.add_argument(
        '--results-dir',
        type=str,
        default='projects/PROJ-586-social-memory-networks-modeling-collecti/results',
        help='Directory containing scaling results JSON file'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='projects/PROJ-586-social-memory-networks-modeling-collecti/results/scaling_plot.pdf',
        help='Output path for the generated PDF plot'
    )
    parser.add_argument(
        '--note',
        type=str,
        default='3 data points limit power-law reliability',
        help='Text note to display about data limitations'
    )
    return parser


def main(args: Optional[argparse.Namespace] = None) -> None:
    """Main entry point for scaling plot generation."""
    parser = build_parser()
    parsed_args = parser.parse_args() if args is None else args

    results_dir = Path(parsed_args.results_dir)
    output_path = Path(parsed_args.output)

    try:
        results = load_scaling_results_for_plot(results_dir)
        generate_scaling_plot_with_notes(results, output_path, parsed_args.note)
        print("Scaling plot generation completed successfully.")
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON results: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()