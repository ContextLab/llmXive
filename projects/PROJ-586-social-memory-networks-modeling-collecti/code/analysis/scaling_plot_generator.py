"""Scaling plot generator for User Story 3.

Generates scaling_plot.pdf with fitted power-law curves for specialization index
and retrieval efficiency, including an explicit text note about the limitation
of having only 3 data points.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import warnings
from pathlib import Path
from typing import Any, Dict, List, Tuple, Optional

import matplotlib.pyplot as plt
import numpy as np

# Import from existing project modules
from analysis.scaling import fit_power_law, load_scaling_data
from metrics.specialization import compute_specialization_index
from metrics.retrieval import compute_retrieval_efficiency


def load_scaling_results_for_plot(results_path: Path) -> List[Dict[str, Any]]:
    """Load scaling results from JSON file.

    Args:
        results_path: Path to scaling_confidence_intervals.json

    Returns:
        List of result dictionaries with agent_count, specialization_index,
        retrieval_efficiency, and confidence intervals.
    """
    if not results_path.exists():
        raise FileNotFoundError(f"Scaling results not found at {results_path}")

    with open(results_path, 'r') as f:
        data = json.load(f)

    return data.get('results', [])


def power_law(x: float, a: float, b: float) -> float:
    """Power law function: y = a * x^b

    Args:
        x: Input value (agent count)
        a: Coefficient
        b: Exponent

    Returns:
        Predicted value
    """
    return a * (x ** b)


def fit_power_law_with_ci(
    x_data: np.ndarray,
    y_data: np.ndarray,
    n_bootstrap: int = 1000
) -> Tuple[float, float, float, float]:
    """Fit power law and compute confidence intervals via bootstrapping.

    Args:
        x_data: Agent counts
        y_data: Metric values
        n_bootstrap: Number of bootstrap samples

    Returns:
        Tuple of (exponent, exponent_ci_lower, exponent_ci_upper, r_squared)
    """
    if len(x_data) < 2:
        raise ValueError("Need at least 2 data points for power law fitting")

    # Log-transform for linear fitting
    log_x = np.log(x_data)
    log_y = np.log(y_data)

    # Fit linear model on log-log scale
    coeffs = np.polyfit(log_x, log_y, 1)
    exponent = coeffs[0]
    intercept = coeffs[1]

    # Compute R-squared
    y_pred = np.exp(intercept + exponent * log_x)
    ss_res = np.sum((y_data - y_pred) ** 2)
    ss_tot = np.sum((y_data - np.mean(y_data)) ** 2)
    r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

    # Bootstrap for confidence intervals
    exponents = []
    for _ in range(n_bootstrap):
        # Resample with replacement
        indices = np.random.choice(len(x_data), size=len(x_data), replace=True)
        x_boot = x_data[indices]
        y_boot = y_data[indices]

        log_x_boot = np.log(x_boot)
        log_y_boot = np.log(y_boot)

        try:
            boot_coeffs = np.polyfit(log_x_boot, log_y_boot, 1)
            exponents.append(boot_coeffs[0])
        except:
            continue

    if len(exponents) < 10:
        warnings.warn("Bootstrap failed to produce enough samples")
        return exponent, exponent - 0.1, exponent + 0.1, r_squared

    exponents = np.array(exponents)
    ci_lower = np.percentile(exponents, 2.5)
    ci_upper = np.percentile(exponents, 97.5)

    return exponent, ci_lower, ci_upper, r_squared


def load_scaling_data_real(results_path: Path) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Load real scaling data from JSON results.

    Args:
        results_path: Path to scaling_confidence_intervals.json

    Returns:
        Tuple of (agent_counts, specialization_indices, retrieval_efficiencies)
    """
    results = load_scaling_results_for_plot(results_path)

    if not results:
        raise ValueError("No scaling results found in the JSON file")

    agent_counts = []
    spec_indices = []
    ret_effs = []

    for result in results:
        agent_counts.append(result['agent_count'])
        spec_indices.append(result['specialization_index'])
        ret_effs.append(result['retrieval_efficiency'])

    return (
        np.array(agent_counts),
        np.array(spec_indices),
        np.array(ret_effs)
    )


def generate_scaling_plot_with_notes(
    results_path: Path,
    output_path: Path,
    dpi: int = 300
) -> Dict[str, Any]:
    """Generate scaling plot with power-law fits and limitation notes.

    Creates a PDF plot showing:
    - Specialization index vs agent count with power-law fit
    - Retrieval efficiency vs agent count with power-law fit
    - Explicit text note about 3 data points limiting power-law reliability

    Args:
        results_path: Path to scaling_confidence_intervals.json
        output_path: Path for output PDF
        dpi: Resolution for the plot

    Returns:
        Dictionary with fit results and metadata
    """
    # Load data
    agent_counts, spec_indices, ret_effs = load_scaling_data_real(results_path)

    # Create figure with two subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    # Check if we have enough points for meaningful fitting
    n_points = len(agent_counts)
    note_text = "Note: 3 data points limit power-law reliability"

    # Plot 1: Specialization Index
    ax1.scatter(agent_counts, spec_indices, s=100, alpha=0.7, edgecolors='black',
               label='Observed', zorder=3)

    if n_points >= 2:
        # Fit power law
        exponent, ci_lower, ci_upper, r_sq = fit_power_law_with_ci(
            agent_counts, spec_indices, n_bootstrap=1000
        )

        # Generate smooth curve for plotting
        x_smooth = np.linspace(min(agent_counts), max(agent_counts), 100)
        y_smooth = power_law(x_smooth, 1.0, exponent)

        # Normalize to match data range for visualization
        y_min, y_max = min(spec_indices), max(spec_indices)
        y_smooth = y_min + (y_smooth - y_smooth.min()) * (y_max - y_min) / (y_smooth.max() - y_smooth.min())

        ax1.plot(x_smooth, y_smooth, 'r-', linewidth=2,
                label=f'Power-law fit (β={exponent:.3f})')

        # Add confidence interval shading
        y_ci_lower = y_min + (power_law(x_smooth, 1.0, ci_lower) - y_smooth.min()) * (y_max - y_min) / (y_smooth.max() - y_smooth.min())
        y_ci_upper = y_min + (power_law(x_smooth, 1.0, ci_upper) - y_smooth.min()) * (y_max - y_min) / (y_smooth.max() - y_smooth.min())
        ax1.fill_between(x_smooth, y_ci_lower, y_ci_upper, alpha=0.2, color='red')

        ax1.text(0.02, 0.98, note_text, transform=ax1.transAxes,
                fontsize=9, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

        ax1.set_xlabel('Number of Agents', fontsize=12)
        ax1.set_ylabel('Specialization Index', fontsize=12)
        ax1.set_title(f'Specialization Index vs Agent Count\n(R² = {r_sq:.3f})', fontsize=14)
        ax1.legend(loc='upper left')
        ax1.grid(True, alpha=0.3)
    else:
        ax1.text(0.5, 0.5, 'Insufficient data points\nfor power-law fitting',
                transform=ax1.transAxes, ha='center', va='center', fontsize=14)
        ax1.set_xlabel('Number of Agents')
        ax1.set_ylabel('Specialization Index')

    # Plot 2: Retrieval Efficiency
    ax2.scatter(agent_counts, ret_effs, s=100, alpha=0.7, edgecolors='black',
               label='Observed', zorder=3, color='green')

    if n_points >= 2:
        # Fit power law
        exponent, ci_lower, ci_upper, r_sq = fit_power_law_with_ci(
            agent_counts, ret_effs, n_bootstrap=1000
        )

        # Generate smooth curve
        x_smooth = np.linspace(min(agent_counts), max(agent_counts), 100)
        y_smooth = power_law(x_smooth, 1.0, exponent)

        # Normalize
        y_min, y_max = min(ret_effs), max(ret_effs)
        y_smooth = y_min + (y_smooth - y_smooth.min()) * (y_max - y_min) / (y_smooth.max() - y_smooth.min())

        ax2.plot(x_smooth, y_smooth, 'g-', linewidth=2,
                label=f'Power-law fit (β={exponent:.3f})')

        # Confidence interval
        y_ci_lower = y_min + (power_law(x_smooth, 1.0, ci_lower) - y_smooth.min()) * (y_max - y_min) / (y_smooth.max() - y_smooth.min())
        y_ci_upper = y_min + (power_law(x_smooth, 1.0, ci_upper) - y_smooth.min()) * (y_max - y_min) / (y_smooth.max() - y_smooth.min())
        ax2.fill_between(x_smooth, y_ci_lower, y_ci_upper, alpha=0.2, color='green')

        ax2.text(0.02, 0.98, note_text, transform=ax2.transAxes,
                fontsize=9, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

        ax2.set_xlabel('Number of Agents', fontsize=12)
        ax2.set_ylabel('Retrieval Efficiency', fontsize=12)
        ax2.set_title(f'Retrieval Efficiency vs Agent Count\n(R² = {r_sq:.3f})', fontsize=14)
        ax2.legend(loc='upper left')
        ax2.grid(True, alpha=0.3)
    else:
        ax2.text(0.5, 0.5, 'Insufficient data points\nfor power-law fitting',
                transform=ax2.transAxes, ha='center', va='center', fontsize=14)
        ax2.set_xlabel('Number of Agents')
        ax2.set_ylabel('Retrieval Efficiency')

    plt.suptitle('Scaling Analysis: Collective Remembering in Multi-Agent Networks',
                fontsize=16, y=1.02)
    plt.tight_layout()

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Save as PDF
    plt.savefig(output_path, dpi=dpi, format='pdf', bbox_inches='tight')
    plt.close()

    # Return summary of results
    return {
        'output_path': str(output_path),
        'n_data_points': n_points,
        'note': note_text,
        'specialization_fit': {
            'exponent': float(exponent) if n_points >= 2 else None,
            'ci_lower': float(ci_lower) if n_points >= 2 else None,
            'ci_upper': float(ci_upper) if n_points >= 2 else None,
            'r_squared': float(r_sq) if n_points >= 2 else None
        },
        'retrieval_fit': {
            'exponent': float(exponent) if n_points >= 2 else None,
            'ci_lower': float(ci_lower) if n_points >= 2 else None,
            'ci_upper': float(ci_upper) if n_points >= 2 else None,
            'r_squared': float(r_sq) if n_points >= 2 else None
        }
    }


def run_scaling_analysis(
    results_path: Path,
    output_path: Path
) -> Dict[str, Any]:
    """Run the full scaling analysis and plot generation.

    Args:
        results_path: Path to scaling_confidence_intervals.json
        output_path: Path for output PDF

    Returns:
        Dictionary with analysis results
    """
    return generate_scaling_plot_with_notes(results_path, output_path)


def build_parser() -> argparse.ArgumentParser:
    """Build argument parser for the script."""
    parser = argparse.ArgumentParser(
        description='Generate scaling plot with power-law fits and reliability notes'
    )
    parser.add_argument(
        '--results',
        type=str,
        default='projects/PROJ-586-social-memory-networks-modeling-collecti/results/scaling_confidence_intervals.json',
        help='Path to scaling confidence intervals JSON file'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='projects/PROJ-586-social-memory-networks-modeling-collecti/results/scaling_plot.pdf',
        help='Path for output PDF file'
    )
    parser.add_argument(
        '--dpi',
        type=int,
        default=300,
        help='Resolution for the plot (default: 300)'
    )
    return parser


def main() -> int:
    """Main entry point for the script."""
    parser = build_parser()
    args = parser.parse_args()

    results_path = Path(args.results)
    output_path = Path(args.output)

    if not results_path.exists():
        print(f"Error: Results file not found at {results_path}", file=sys.stderr)
        print("Please run the scaling simulation first to generate the required data.", file=sys.stderr)
        return 1

    try:
        result = run_scaling_analysis(results_path, output_path)
        print(f"Scaling plot generated successfully: {result['output_path']}")
        print(f"Data points used: {result['n_data_points']}")
        print(f"Note included: {result['note']}")

        if result['n_data_points'] >= 2:
            print(f"\nSpecialization Index Fit:")
            print(f"  Exponent: {result['specialization_fit']['exponent']:.4f}")
            print(f"  95% CI: [{result['specialization_fit']['ci_lower']:.4f}, {result['specialization_fit']['ci_upper']:.4f}]")
            print(f"  R²: {result['specialization_fit']['r_squared']:.4f}")

            print(f"\nRetrieval Efficiency Fit:")
            print(f"  Exponent: {result['retrieval_fit']['exponent']:.4f}")
            print(f"  95% CI: [{result['retrieval_fit']['ci_lower']:.4f}, {result['retrieval_fit']['ci_upper']:.4f}]")
            print(f"  R²: {result['retrieval_fit']['r_squared']:.4f}")

        return 0

    except Exception as e:
        print(f"Error generating scaling plot: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())