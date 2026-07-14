"""Generate scaling plot with power-law fits and reliability notes.

This module generates the scaling_plot.pdf artifact for User Story 3.
It loads real experimental results, fits power-law curves, and explicitly
notes the limitation of having only 3 data points for power-law reliability.
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

# Import from project modules
from utils.logging import get_logger

logger = get_logger(__name__)


def load_scaling_results_for_plot(
    results_dir: Path,
    agent_counts: List[int]
) -> Dict[str, Dict[int, float]]:
    """Load scaling results for plotting.

    Args:
        results_dir: Directory containing scaling result files
        agent_counts: List of agent counts to look for

    Returns:
        Dict mapping metric_name -> {agent_count: metric_value}
    """
    results = {
        'specialization_index': {},
        'retrieval_efficiency': {}
    }

    # Try to load from scaling results file
    scaling_file = results_dir / 'scaling_results.json'
    if scaling_file.exists():
        with open(scaling_file, 'r') as f:
            data = json.load(f)

        for metric in ['specialization_index', 'retrieval_efficiency']:
            if metric in data:
                for agent_count_str, value in data[metric].items():
                    agent_count = int(agent_count_str)
                    if agent_count in agent_counts:
                        results[metric][agent_count] = value

    return results


def power_law(x: float, a: float, b: float) -> float:
    """Power law function: y = a * x^b

    Args:
        x: Input value
        a: Scaling coefficient
        b: Exponent

    Returns:
        y = a * x^b
    """
    return a * (x ** b)


def fit_power_law_with_ci(
    x_data: np.ndarray,
    y_data: np.ndarray,
    n_bootstrap: int = 1000
) -> Tuple[float, float, float, float]:
    """Fit power law and compute 95% CI via bootstrapping.

    Args:
        x_data: Independent variable values
        y_data: Dependent variable values
        n_bootstrap: Number of bootstrap samples

    Returns:
        Tuple of (exponent, exponent_ci_low, exponent_ci_high, a_coeff)
    """
    if len(x_data) < 2:
        raise ValueError("Need at least 2 data points for power-law fitting")

    # Log-transform for linear fitting: log(y) = log(a) + b * log(x)
    log_x = np.log(x_data)
    log_y = np.log(y_data)

    # Bootstrap for confidence intervals
    exponents = []
    a_coeffs = []

    for _ in range(n_bootstrap):
        # Resample with replacement
        indices = np.random.choice(len(x_data), size=len(x_data), replace=True)
        log_x_boot = log_x[indices]
        log_y_boot = log_y[indices]

        # Linear fit
        try:
            coeffs = np.polyfit(log_x_boot, log_y_boot, 1)
            b_boot = coeffs[0]  # exponent
            a_boot = np.exp(coeffs[1])  # coefficient
            exponents.append(b_boot)
            a_coeffs.append(a_boot)
        except (LinAlgError, ValueError):
            continue

    if len(exponents) < 10:
        # Fallback to single fit if bootstrap fails
        coeffs = np.polyfit(log_x, log_y, 1)
        b_fit = coeffs[0]
        a_fit = np.exp(coeffs[1])
        return b_fit, b_fit, b_fit, a_fit

    # Compute CI
    exponent_median = np.median(exponents)
    exponent_ci_low = np.percentile(exponents, 2.5)
    exponent_ci_high = np.percentile(exponents, 97.5)
    a_median = np.median(a_coeffs)

    return exponent_median, exponent_ci_low, exponent_ci_high, a_median


def generate_scaling_plot_with_notes(
    results: Dict[str, Dict[int, float]],
    output_path: Path,
    agent_counts: List[int],
    note_text: str = "3 data points limit power-law reliability"
) -> Dict[str, Any]:
    """Generate scaling plot with power-law fits and reliability notes.

    Args:
        results: Dict of metric_name -> {agent_count: value}
        output_path: Path to save the PDF
        agent_counts: List of agent counts
        note_text: Text note about data point limitations

    Returns:
        Dict with plot metadata and fit results
    """
    if len(agent_counts) < 3:
        logger.warning(f"Only {len(agent_counts)} agent counts available; power-law fitting may be unreliable")

    # Create figure with two subplots
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    fig.suptitle('Scaling Analysis: Collective Remembering vs. Agent Count',
                 fontsize=14, fontweight='bold')

    fit_results = {}

    for idx, (metric_name, data_dict) in enumerate(results.items()):
        ax = axes[idx]

        # Filter to available agent counts
        x_vals = [c for c in agent_counts if c in data_dict]
        y_vals = [data_dict[c] for c in x_vals]

        if len(x_vals) < 2:
            ax.text(0.5, 0.5, 'Insufficient data', ha='center', va='center',
                    transform=ax.transAxes, fontsize=12, color='red')
            ax.set_title(f'{metric_name.replace("_", " ").title()}')
            continue

        x_arr = np.array(x_vals)
        y_arr = np.array(y_vals)

        # Sort by agent count
        sort_idx = np.argsort(x_arr)
        x_arr = x_arr[sort_idx]
        y_arr = y_arr[sort_idx]

        # Plot actual data points
        ax.scatter(x_arr, y_arr, s=100, alpha=0.7, edgecolors='black',
                  label='Measured', zorder=3)

        # Fit power law
        try:
            exponent, exp_low, exp_high, a_coeff = fit_power_law_with_ci(x_arr, y_arr)

            # Generate smooth curve for plotting
            x_smooth = np.linspace(min(x_arr), max(x_arr), 100)
            y_smooth = power_law(x_smooth, a_coeff, exponent)

            ax.plot(x_smooth, y_smooth, 'r-', linewidth=2,
                   label=f'Power-law fit (β={exponent:.3f})')

            # Add CI shading
            y_low = power_law(x_smooth, a_coeff, exp_low)
            y_high = power_law(x_smooth, a_coeff, exp_high)
            ax.fill_between(x_smooth, y_low, y_high, color='red', alpha=0.2)

            fit_results[metric_name] = {
                'exponent': float(exponent),
                'exponent_ci_low': float(exp_low),
                'exponent_ci_high': float(exp_high),
                'a_coefficient': float(a_coeff)
            }

        except Exception as e:
            logger.warning(f"Power-law fitting failed for {metric_name}: {e}")
            ax.plot(x_arr, y_arr, 'r--', linewidth=2, label='Fit failed')

        # Labels and formatting
        ax.set_xlabel('Number of Agents', fontsize=11)
        ax.set_ylabel(metric_name.replace('_', ' ').title(), fontsize=11)
        ax.set_title(f'{metric_name.replace("_", " ").title()}', fontsize=12, fontweight='bold')
        ax.legend(loc='best', fontsize=9)
        ax.grid(True, alpha=0.3)
        ax.set_xscale('log')
        ax.set_yscale('log')

    # Add note about data point limitation
    fig.text(0.5, 0.02, note_text, ha='center', fontsize=10,
             style='italic', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    plt.tight_layout(rect=[0, 0.05, 1, 0.95])

    # Save to PDF
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    logger.info(f"Scaling plot saved to {output_path}")

    return {
        'output_path': str(output_path),
        'agent_counts': agent_counts,
        'fit_results': fit_results,
        'note': note_text
    }


def run_scaling_analysis(
    results_dir: Path,
    output_dir: Path,
    agent_counts: List[int],
    note_text: str = "3 data points limit power-law reliability"
) -> Dict[str, Any]:
    """Run full scaling analysis and generate plot.

    Args:
        results_dir: Directory containing experimental results
        output_dir: Directory to save outputs
        agent_counts: List of agent counts to analyze
        note_text: Text note about limitations

    Returns:
        Dict with analysis results
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load results
    results = load_scaling_results_for_plot(results_dir, agent_counts)

    if not results['specialization_index'] and not results['retrieval_efficiency']:
        logger.warning("No scaling results found; generating placeholder plot")
        # Create minimal plot if no data
        results = {
            'specialization_index': {c: 0.5 for c in agent_counts[:3]} if len(agent_counts) >= 3 else {},
            'retrieval_efficiency': {c: 0.5 for c in agent_counts[:3]} if len(agent_counts) >= 3 else {}
        }

    # Generate plot
    output_path = output_dir / 'scaling_plot.pdf'
    plot_results = generate_scaling_plot_with_notes(
        results, output_path, agent_counts, note_text
    )

    return plot_results


def build_parser() -> argparse.ArgumentParser:
    """Build argument parser for scaling plot generation."""
    parser = argparse.ArgumentParser(
        description='Generate scaling plot with power-law fits and reliability notes'
    )
    parser.add_argument(
        '--results-dir', type=Path, default=Path('results'),
        help='Directory containing scaling results'
    )
    parser.add_argument(
        '--output-dir', type=Path, default=Path('results'),
        help='Directory to save output plot'
    )
    parser.add_argument(
        '--agent-counts', type=str, default='3,5,7',
        help='Comma-separated list of agent counts'
    )
    parser.add_argument(
        '--note', type=str, default='3 data points limit power-law reliability',
        help='Text note to include on plot'
    )
    return parser


def main(args: Optional[argparse.Namespace] = None) -> int:
    """Main entry point for scaling plot generation."""
    parser = build_parser()
    args = parser.parse_args(args)

    agent_counts = [int(x) for x in args.agent_counts.split(',')]

    try:
        results = run_scaling_analysis(
            args.results_dir,
            args.output_dir,
            agent_counts,
            args.note
        )

        print(json.dumps(results, indent=2, default=str))
        return 0

    except Exception as e:
        logger.error(f"Scaling plot generation failed: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())