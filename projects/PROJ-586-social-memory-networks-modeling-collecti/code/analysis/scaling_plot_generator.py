"""Scaling plot generator for User Story 3.

Generates a PDF plot of specialization index and retrieval efficiency vs. agent count,
with fitted power-law curves and an explicit note about the limitation of 3 data points.
"""
from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for PDF generation
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.optimize import curve_fit

# Ensure project root is in path for imports
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


@dataclass
class ScalingPlotResult:
    """Result of scaling plot generation."""
    plot_path: str
    success: bool
    message: str
    exponent_specialization: Optional[float] = None
    exponent_retrieval: Optional[float] = None


def power_law(x: np.ndarray, a: float, b: float) -> np.ndarray:
    """Power law function: y = a * x^b."""
    return a * np.power(x, b)


def load_scaling_data_from_csv(csv_path: str) -> pd.DataFrame:
    """Load scaling data from CSV file.

    Expected columns: agent_count, specialization_index, retrieval_efficiency
    """
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"Scaling data file not found: {csv_path}")

    df = pd.read_csv(path)
    required_cols = {'agent_count', 'specialization_index', 'retrieval_efficiency'}
    if not required_cols.issubset(df.columns):
        missing = required_cols - set(df.columns)
        raise ValueError(f"Missing required columns in scaling data: {missing}")

    return df


def generate_scaling_plot_with_notes(
    data_path: str,
    output_path: str,
    x_limits: Optional[Tuple[float, float]] = None,
    y_limits: Optional[Tuple[float, float]] = None
) -> ScalingPlotResult:
    """Generate scaling plot with power-law fits and limitation notes.

    Args:
        data_path: Path to CSV with scaling data
        output_path: Path for output PDF
        x_limits: Optional (min, max) for x-axis
        y_limits: Optional (min, max) for y-axis

    Returns:
        ScalingPlotResult with plot path and metadata
    """
    try:
        # Load data
        df = load_scaling_data_from_csv(data_path)

        # Sort by agent count for consistent plotting
        df = df.sort_values('agent_count').reset_index(drop=True)

        agent_counts = df['agent_count'].values
        spec_indices = df['specialization_index'].values
        retrieval_effs = df['retrieval_efficiency'].values

        # Filter out NaN values for fitting
        valid_mask = ~np.isnan(spec_indices) & ~np.isnan(retrieval_effs)
        agent_counts_valid = agent_counts[valid_mask]
        spec_indices_valid = spec_indices[valid_mask]
        retrieval_effs_valid = retrieval_effs[valid_mask]

        if len(agent_counts_valid) < 2:
            return ScalingPlotResult(
                plot_path=output_path,
                success=False,
                message="Insufficient valid data points for fitting (need at least 2)"
            )

        # Create figure with two subplots
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

        # Fit power law for specialization index
        exp_spec = None
        if len(agent_counts_valid) >= 2:
            try:
                popt_spec, _ = curve_fit(
                    power_law,
                    agent_counts_valid,
                    spec_indices_valid,
                    p0=[1.0, 0.0],
                    maxfev=5000
                )
                exp_spec = popt_spec[1]

                # Generate smooth curve for plotting
                x_smooth = np.linspace(agent_counts_valid.min(), agent_counts_valid.max(), 100)
                y_smooth_spec = power_law(x_smooth, popt_spec[0], popt_spec[1])
                ax1.plot(x_smooth, y_smooth_spec, 'r--', alpha=0.7,
                        label=f'Power-law fit (β={exp_spec:.3f})')
            except Exception as e:
                ax1.plot([], [], 'r--', alpha=0.7, label='Fit failed')

        # Plot specialization data points
        ax1.scatter(agent_counts_valid, spec_indices_valid, c='blue', s=100, zorder=5,
                   label='Measured data', edgecolors='black')
        ax1.set_xlabel('Number of Agents', fontsize=12)
        ax1.set_ylabel('Specialization Index', fontsize=12)
        ax1.set_title('Specialization Index vs. Agent Count', fontsize=14)
        ax1.legend(loc='best')
        ax1.grid(True, alpha=0.3)

        if x_limits:
            ax1.set_xlim(x_limits)
        if y_limits:
            ax1.set_ylim(y_limits)

        # Fit power law for retrieval efficiency
        exp_ret = None
        if len(agent_counts_valid) >= 2:
            try:
                popt_ret, _ = curve_fit(
                    power_law,
                    agent_counts_valid,
                    retrieval_effs_valid,
                    p0=[1.0, 0.0],
                    maxfev=5000
                )
                exp_ret = popt_ret[1]

                # Generate smooth curve for plotting
                x_smooth = np.linspace(agent_counts_valid.min(), agent_counts_valid.max(), 100)
                y_smooth_ret = power_law(x_smooth, popt_ret[0], popt_ret[1])
                ax2.plot(x_smooth, y_smooth_ret, 'g--', alpha=0.7,
                        label=f'Power-law fit (β={exp_ret:.3f})')
            except Exception as e:
                ax2.plot([], [], 'g--', alpha=0.7, label='Fit failed')

        # Plot retrieval efficiency data points
        ax2.scatter(agent_counts_valid, retrieval_effs_valid, c='orange', s=100, zorder=5,
                   label='Measured data', edgecolors='black')
        ax2.set_xlabel('Number of Agents', fontsize=12)
        ax2.set_ylabel('Retrieval Efficiency', fontsize=12)
        ax2.set_title('Retrieval Efficiency vs. Agent Count', fontsize=14)
        ax2.legend(loc='best')
        ax2.grid(True, alpha=0.3)

        if x_limits:
            ax2.set_xlim(x_limits)
        if y_limits:
            ax2.set_ylim(y_limits)

        # Add explicit note about 3 data points limitation
        note_text = (
            "Note: Scaling analysis based on 3 agent counts (3, 5, 7).\n"
            "Power-law fitting with only 3 data points has limited statistical\n"
            "reliability. Results should be interpreted as preliminary trends\n"
            "rather than definitive scaling laws. More agent counts are needed\n"
            "for robust power-law validation."
        )

        # Add note to figure
        fig.text(
            0.5, 0.02,
            note_text,
            fontsize=10,
            ha='center',
            va='bottom',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5, edgecolor='gray')
        )

        # Adjust layout to make room for the note
        plt.tight_layout(rect=[0, 0.12, 1, 1])

        # Ensure output directory exists
        output_dir = Path(output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save as PDF
        plt.savefig(output_path, format='pdf', bbox_inches='tight', dpi=150)
        plt.close(fig)

        return ScalingPlotResult(
            plot_path=output_path,
            success=True,
            message=f"Plot generated successfully: {output_path}",
            exponent_specialization=exp_spec,
            exponent_retrieval=exp_ret
        )

    except Exception as e:
        return ScalingPlotResult(
            plot_path=output_path,
            success=False,
            message=f"Error generating plot: {str(e)}"
        )


def build_parser() -> argparse.ArgumentParser:
    """Build argument parser for the script."""
    parser = argparse.ArgumentParser(
        description="Generate scaling plot with power-law fits and limitation notes"
    )
    parser.add_argument(
        "--input",
        type=str,
        default="data/scaling_results.csv",
        help="Path to input CSV file with scaling data"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="projects/PROJ-586-social-memory-networks-modeling-collecti/results/scaling_plot.pdf",
        help="Path for output PDF file"
    )
    parser.add_argument(
        "--x-limits",
        type=float,
        nargs=2,
        metavar=('MIN', 'MAX'),
        help="X-axis limits (min max)"
    )
    parser.add_argument(
        "--y-limits",
        type=float,
        nargs=2,
        metavar=('MIN', 'MAX'),
        help="Y-axis limits (min max)"
    )
    return parser


def main() -> int:
    """Main entry point."""
    parser = build_parser()
    args = parser.parse_args()

    result = generate_scaling_plot_with_notes(
        data_path=args.input,
        output_path=args.output,
        x_limits=tuple(args.x_limits) if args.x_limits else None,
        y_limits=tuple(args.y_limits) if args.y_limits else None
    )

    print(result.message)
    return 0 if result.success else 1


if __name__ == "__main__":
    sys.exit(main())
