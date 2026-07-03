"""Generate scaling plot with power-law fit and reliability note.

This module generates the scaling plot for User Story 3, plotting specialization
index and retrieval efficiency against agent count (3, 5, 7). It includes a
fitted power-law curve and an explicit note about the limitation of 3 data points.
"""
from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for CI
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

# Ensure output directory exists
OUTPUT_DIR = Path("projects/PROJ-586-social-memory-networks-modeling-collecti/results")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class ScalingPlotResult:
    """Result of the scaling plot generation."""
    plot_path: str
    fitted_exponent_specialization: Optional[float]
    fitted_exponent_retrieval: Optional[float]
    data_points: int
    note_included: bool


def power_law(x: np.ndarray, a: float, b: float) -> np.ndarray:
    """Power law function: y = a * x^b."""
    return a * np.power(x, b)


def load_scaling_data() -> pd.DataFrame:
    """Load scaling experiment results from CSV.

    Expects a CSV with columns: agent_count, specialization_index, retrieval_efficiency
    """
    # Try to load from the expected results directory
    csv_path = OUTPUT_DIR / "scaling_results.csv"
    
    if not csv_path.exists():
        # Fallback to data directory if results not in OUTPUT_DIR
        fallback_path = Path("data/scaling_results.csv")
        if fallback_path.exists():
            csv_path = fallback_path
        else:
            raise FileNotFoundError(
                f"Scaling results CSV not found at {csv_path} or {fallback_path}. "
                "Run the scaling experiment first."
            )
    
    df = pd.read_csv(csv_path)
    
    # Ensure we have the required columns
    required_cols = ['agent_count', 'specialization_index', 'retrieval_efficiency']
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required column '{col}' in scaling results")
    
    return df


def fit_power_law_data(
    x: np.ndarray, 
    y: np.ndarray,
    x_label: str
) -> Tuple[Optional[float], Optional[float]]:
    """Fit power law to data and return (a, b) parameters.
    
    Returns (None, None) if fitting fails.
    """
    try:
        # Filter out zero/negative values for log fitting
        valid_mask = (x > 0) & (y > 0)
        if np.sum(valid_mask) < 3:
            print(f"Warning: Not enough valid data points for {x_label} fitting")
            return None, None
        
        x_valid = x[valid_mask]
        y_valid = y[valid_mask]
        
        # Initial guess: a=1, b=0 (flat line)
        p0 = [1.0, 0.0]
        
        # Fit power law
        popt, _ = curve_fit(power_law, x_valid, y_valid, p0=p0, maxfev=10000)
        return popt[0], popt[1]
    except Exception as e:
        print(f"Warning: Power law fitting failed for {x_label}: {e}")
        return None, None


def generate_scaling_plot_with_notes(
    output_path: Optional[Path] = None
) -> ScalingPlotResult:
    """Generate the scaling plot with power-law fit and reliability note.
    
    Args:
        output_path: Path to save the PDF. Defaults to OUTPUT_DIR/scaling_plot.pdf
        
    Returns:
        ScalingPlotResult with metadata about the plot
    """
    if output_path is None:
        output_path = OUTPUT_DIR / "scaling_plot.pdf"
        
    # Load data
    df = load_scaling_data()
    
    # Aggregate by agent_count (take mean if multiple runs)
    agg_df = df.groupby('agent_count').agg({
        'specialization_index': 'mean',
        'retrieval_efficiency': 'mean'
    }).reset_index()
    
    agent_counts = agg_df['agent_count'].values.astype(float)
    spec_indices = agg_df['specialization_index'].values.astype(float)
    ret_effs = agg_df['retrieval_efficiency'].values.astype(float)
    
    # Fit power laws
    a_spec, b_spec = fit_power_law_data(agent_counts, spec_indices, "specialization")
    a_ret, b_ret = fit_power_law_data(agent_counts, ret_effs, "retrieval")
    
    # Generate smooth curve for plotting
    x_smooth = np.linspace(min(agent_counts), max(agent_counts), 100)
    
    # Create figure
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Plot specialization index
    if a_spec is not None and b_spec is not None:
        y_spec_fit = power_law(x_smooth, a_spec, b_spec)
        ax.plot(x_smooth, y_spec_fit, 'r-', linewidth=2, label=f'Specialization fit (β={b_spec:.3f})')
    
    ax.scatter(agent_counts, spec_indices, c='red', s=100, zorder=5, label='Specialization Index')
    
    # Plot retrieval efficiency (secondary y-axis)
    ax2 = ax.twinx()
    if a_ret is not None and b_ret is not None:
        y_ret_fit = power_law(x_smooth, a_ret, b_ret)
        ax2.plot(x_smooth, y_ret_fit, 'b-', linewidth=2, label=f'Retrieval fit (β={b_ret:.3f})')
    
    ax2.scatter(agent_counts, ret_effs, c='blue', s=100, zorder=5, label='Retrieval Efficiency')
    
    # Labels and title
    ax.set_xlabel('Number of Agents', fontsize=12)
    ax.set_ylabel('Specialization Index', color='red', fontsize=12)
    ax2.set_ylabel('Retrieval Efficiency', color='blue', fontsize=12)
    ax.set_title('Scaling of Collective Remembering Metrics with Agent Count', fontsize=14)
    
    # Combine legends
    lines_1, labels_1 = ax.get_legend_handles_labels()
    lines_2, labels_2 = ax2.get_legend_handles_labels()
    ax.legend(lines_1 + lines_2, labels_1 + labels_2, loc='upper left')
    
    # Grid
    ax.grid(True, alpha=0.3)
    
    # Add explicit note about 3 data points limitation
    note_text = (
        "Note: Power-law fit based on only 3 data points (N=3, 5, 7).\n"
        "This limits the statistical reliability of the exponent estimate."
    )
    fig.text(
        0.5, 0.02, 
        note_text, 
        ha='center', 
        fontsize=10, 
        style='italic',
        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5)
    )
    
    # Adjust layout to make room for the note
    plt.tight_layout(rect=[0, 0.08, 1, 1])
    
    # Save
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    
    return ScalingPlotResult(
        plot_path=str(output_path),
        fitted_exponent_specialization=b_spec,
        fitted_exponent_retrieval=b_ret,
        data_points=len(agent_counts),
        note_included=True
    )


def build_parser() -> argparse.ArgumentParser:
    """Build argument parser for the scaling plot generator."""
    parser = argparse.ArgumentParser(
        description='Generate scaling plot with power-law fit and reliability note.'
    )
    parser.add_argument(
        '--input',
        type=Path,
        default=None,
        help='Path to scaling results CSV (default: auto-detect)'
    )
    parser.add_argument(
        '--output',
        type=Path,
        default=None,
        help='Path to save the PDF plot (default: results/scaling_plot.pdf)'
    )
    return parser


def main(args: Optional[List[str]] = None) -> int:
    """Main entry point."""
    parser = build_parser()
    parsed_args = parser.parse_args(args)
    
    try:
        result = generate_scaling_plot_with_notes(parsed_args.output)
        print(f"Scaling plot generated: {result.plot_path}")
        print(f"  Specialization exponent: {result.fitted_exponent_specialization}")
        print(f"  Retrieval exponent: {result.fitted_exponent_retrieval}")
        print(f"  Data points: {result.data_points}")
        print(f"  Reliability note included: {result.note_included}")
        return 0
    except Exception as e:
        print(f"Error generating scaling plot: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())