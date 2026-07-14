"""Scaling plot generation for User Story 3.

This module generates the scaling_plot.pdf with fitted power-law curves
for specialization index and retrieval efficiency, including the required
textual note about data point limitations.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import warnings
from pathlib import Path
from typing import List, Tuple, Any, Optional

import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for CI
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from analysis.scaling import fit_power_law, load_scaling_data


def load_scaling_results_for_plot(results_dir: Path) -> pd.DataFrame:
    """Load scaling experiment results from JSON files.

    Args:
        results_dir: Directory containing scaling result JSON files.

    Returns:
        DataFrame with agent_count, specialization_index, retrieval_efficiency.
    """
    files = list(results_dir.glob("scaling_results_*.json"))
    if not files:
        # Try alternative naming convention
        files = list(results_dir.glob("*scaling*.json"))

    if not files:
        raise FileNotFoundError(f"No scaling result files found in {results_dir}")

    all_data = []
    for file_path in files:
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            if isinstance(data, list):
                all_data.extend(data)
            elif isinstance(data, dict):
                if 'results' in data:
                    all_data.extend(data['results'])
                else:
                    all_data.append(data)
        except (json.JSONDecodeError, KeyError) as e:
            warnings.warn(f"Failed to parse {file_path}: {e}")

    if not all_data:
        raise ValueError("No valid data found in scaling result files")

    df = pd.DataFrame(all_data)
    required_cols = ['agent_count', 'specialization_index', 'retrieval_efficiency']
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    # Filter out invalid values
    df = df[df['agent_count'] > 0].copy()
    df = df[df['specialization_index'].notna() & (df['specialization_index'] >= 0)]
    df = df[df['retrieval_efficiency'].notna() & (df['retrieval_efficiency'] >= 0)]

    # Group by agent_count and take mean for each metric
    df_grouped = df.groupby('agent_count').agg({
        'specialization_index': 'mean',
        'retrieval_efficiency': 'mean'
    }).reset_index()

    return df_grouped


def generate_scaling_plot_with_notes(
    data: pd.DataFrame,
    output_path: Path,
    x_label: str = "Number of Agents (N)",
    y_label_spec: str = "Specialization Index",
    y_label_ret: str = "Retrieval Efficiency",
    note_text: str = "3 data points limit power-law reliability"
) -> Dict[str, Any]:
    """Generate scaling plot with power-law fits and explanatory note.

    Args:
        data: DataFrame with agent_count, specialization_index, retrieval_efficiency.
        output_path: Path to save the PDF plot.
        x_label: Label for x-axis.
        y_label_spec: Label for specialization y-axis.
        y_label_ret: Label for retrieval y-axis.
        note_text: Text note to include in the plot.

    Returns:
        Dictionary with fit parameters and metadata.
    """
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    agent_counts = data['agent_count'].values
    spec_indices = data['specialization_index'].values
    ret_efficiencies = data['retrieval_efficiency'].values

    n_points = len(agent_counts)

    # Create figure with two subplots
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    fig.suptitle("Scaling Analysis: Collective Remembering Metrics vs. Agent Count",
                 fontsize=14, fontweight='bold')

    # Plot specialization index
    ax1 = axes[0]
    ax1.scatter(agent_counts, spec_indices, c='blue', s=100, alpha=0.7,
               label='Measured', edgecolors='black')

    # Fit power law: y = a * x^b
    # In log space: log(y) = log(a) + b * log(x)
    if n_points >= 2:
        log_x = np.log(agent_counts)
        log_y_spec = np.log(spec_indices + 1e-10)  # Avoid log(0)

        # Simple linear regression in log space
        coeffs_spec = np.polyfit(log_x, log_y_spec, 1)
        beta_spec = coeffs_spec[0]
        alpha_spec = np.exp(coeffs_spec[1])

        # Generate smooth curve for plotting
        x_fit = np.linspace(agent_counts.min(), agent_counts.max(), 100)
        y_fit_spec = alpha_spec * (x_fit ** beta_spec)

        ax1.plot(x_fit, y_fit_spec, 'b-', linewidth=2,
                label=f'Power-law fit: y = {alpha_spec:.3f} * x^{beta_spec:.3f}')
        ax1.set_title(f"Specialization Index (N={n_points} points)")
    else:
        beta_spec = 0.0
        alpha_spec = 0.0
        ax1.set_title(f"Specialization Index (Insufficient points: N={n_points})")

    ax1.set_xlabel(x_label)
    ax1.set_ylabel(y_label_spec)
    ax1.set_xscale('log')
    ax1.set_yscale('log')
    ax1.grid(True, alpha=0.3)
    ax1.legend(loc='upper left')

    # Plot retrieval efficiency
    ax2 = axes[1]
    ax2.scatter(agent_counts, ret_efficiencies, c='green', s=100, alpha=0.7,
               label='Measured', edgecolors='black')

    if n_points >= 2:
        log_x = np.log(agent_counts)
        log_y_ret = np.log(ret_efficiencies + 1e-10)

        coeffs_ret = np.polyfit(log_x, log_y_ret, 1)
        beta_ret = coeffs_ret[0]
        alpha_ret = np.exp(coeffs_ret[1])

        x_fit = np.linspace(agent_counts.min(), agent_counts.max(), 100)
        y_fit_ret = alpha_ret * (x_fit ** beta_ret)

        ax2.plot(x_fit, y_fit_ret, 'g-', linewidth=2,
                label=f'Power-law fit: y = {alpha_ret:.3f} * x^{beta_ret:.3f}')
        ax2.set_title(f"Retrieval Efficiency (N={n_points} points)")
    else:
        beta_ret = 0.0
        alpha_ret = 0.0
        ax2.set_title(f"Retrieval Efficiency (Insufficient points: N={n_points})")

    ax2.set_xlabel(x_label)
    ax2.set_ylabel(y_label_ret)
    ax2.set_xscale('log')
    ax2.set_yscale('log')
    ax2.grid(True, alpha=0.3)
    ax2.legend(loc='upper left')

    # Add the required note about data point limitations
    note_box = (
        f"NOTE: {note_text}\n"
        f"   With only {n_points} data points, power-law exponent estimates\n"
        f"   have high uncertainty. Treat fitted exponents as preliminary."
    )

    fig.text(0.5, 0.02, note_box, fontsize=10, ha='center',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    plt.tight_layout(rect=[0, 0.1, 1, 0.95])

    # Save to PDF
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()

    # Compile results
    results = {
        'output_path': str(output_path),
        'n_data_points': n_points,
        'specialization_fit': {
            'alpha': float(alpha_spec),
            'beta': float(beta_spec),
            'equation': f"y = {alpha_spec:.4f} * x^{beta_spec:.4f}"
        },
        'retrieval_fit': {
            'alpha': float(alpha_ret),
            'beta': float(beta_ret),
            'equation': f"y = {alpha_ret:.4f} * x^{beta_ret:.4f}"
        },
        'note': note_text,
        'warning': f"Power-law reliability limited by {n_points} data points"
    }

    return results


def build_parser() -> argparse.ArgumentParser:
    """Build argument parser for the scaling plot script."""
    parser = argparse.ArgumentParser(
        description="Generate scaling plot with power-law fits"
    )
    parser.add_argument(
        "--results-dir",
        type=Path,
        default=Path("projects/PROJ-586-social-memory-networks-modeling-collecti/results"),
        help="Directory containing scaling result JSON files"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("projects/PROJ-586-social-memory-networks-modeling-collecti/results/scaling_plot.pdf"),
        help="Output path for the PDF plot"
    )
    parser.add_argument(
        "--note",
        type=str,
        default="3 data points limit power-law reliability",
        help="Text note to include in the plot"
    )
    return parser


def main() -> int:
    """Main entry point for scaling plot generation."""
    parser = build_parser()
    args = parser.parse_args()

    try:
        # Load data
        print(f"Loading scaling results from {args.results_dir}...")
        data = load_scaling_results_for_plot(args.results_dir)
        print(f"Loaded {len(data)} data points")

        # Generate plot
        print(f"Generating plot: {args.output}")
        results = generate_scaling_plot_with_notes(
            data=data,
            output_path=args.output,
            note_text=args.note
        )

        # Save results metadata
        metadata_path = args.output.with_suffix('.json')
        with open(metadata_path, 'w') as f:
            json.dump(results, f, indent=2)

        print(f"Plot saved to: {args.output}")
        print(f"Metadata saved to: {metadata_path}")
        print(f"Note included: {results['note']}")

        return 0

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"Data error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())