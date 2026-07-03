"""
Scaling Plot Generator for Social Memory Networks.

Generates scaling_plot.pdf with fitted power-law curves and explicit notes
about the limitation of 3 data points for power-law reliability.
"""
from __future__ import annotations

import argparse
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for server environments
import matplotlib.pyplot as plt

# Ensure results directory exists
RESULTS_DIR = Path("projects/PROJ-586-social-memory-networks-modeling-collecti/results")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class ScalingPlotResult:
    """Container for scaling plot generation results."""
    success: bool
    output_path: Path
    exponent: Optional[float]
    r_squared: Optional[float]
    message: str


def power_law(x: np.ndarray, beta: float) -> np.ndarray:
    """
    Compute power-law function: y = x^beta
    
    Args:
        x: Input array (agent counts)
        beta: Exponent parameter
    
    Returns:
        y values following power law
    """
    return np.power(x, beta)


def fit_power_law_safe(x: np.ndarray, y: np.ndarray) -> Tuple[Optional[float], Optional[float]]:
    """
    Safely fit a power-law model to data using log-log linear regression.
    
    y = A * x^beta  =>  log(y) = log(A) + beta * log(x)
    
    Args:
        x: Agent counts (independent variable)
        y: Metric values (dependent variable)
    
    Returns:
        Tuple of (beta_exponent, r_squared) or (None, None) on failure
    """
    if len(x) < 2 or len(y) < 2:
        return None, None
    
    # Filter out non-positive values (log undefined)
    valid_mask = (x > 0) & (y > 0)
    x_valid = x[valid_mask]
    y_valid = y[valid_mask]
    
    if len(x_valid) < 2:
        return None, None
    
    try:
        # Log-log transformation
        log_x = np.log(x_valid)
        log_y = np.log(y_valid)
        
        # Linear regression: log_y = intercept + beta * log_x
        # Using numpy's polyfit for simplicity
        coeffs = np.polyfit(log_x, log_y, 1)
        beta = coeffs[0]
        intercept = coeffs[1]
        
        # Compute R-squared
        y_pred = np.polyval(coeffs, log_x)
        ss_res = np.sum((log_y - y_pred) ** 2)
        ss_tot = np.sum((log_y - np.mean(log_y)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
        
        return beta, r_squared
    except (ValueError, RuntimeWarning, ZeroDivisionError):
        return None, None


def load_scaling_data_from_csv(input_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Load scaling experiment data from CSV file.
    
    Args:
        input_path: Path to CSV file (defaults to results/scaling_data.csv)
    
    Returns:
        DataFrame with agent_count, specialization_index, retrieval_efficiency columns
    """
    if input_path is None:
        input_path = RESULTS_DIR / "scaling_data.csv"
    
    if not input_path.exists():
        # Try alternative paths
        alt_path = Path("results/scaling_data.csv")
        if alt_path.exists():
            input_path = alt_path
        else:
            raise FileNotFoundError(f"Scaling data not found at {input_path}")
    
    df = pd.read_csv(input_path)
    
    # Ensure required columns exist
    required_cols = ['agent_count', 'specialization_index', 'retrieval_efficiency']
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")
    
    return df


def generate_scaling_plot_with_notes(
    input_path: Optional[Path] = None,
    output_path: Optional[Path] = None,
    dpi: int = 300
) -> ScalingPlotResult:
    """
    Generate scaling plot with power-law fits and reliability notes.
    
    Creates a PDF plot showing:
    1. Scatter plots of specialization_index and retrieval_efficiency vs agent_count
    2. Fitted power-law curves
    3. Explicit note about 3 data points limiting power-law reliability
    
    Args:
        input_path: Path to input scaling data CSV
        output_path: Path to output PDF file
        dpi: Resolution for the plot
    
    Returns:
        ScalingPlotResult with success status and details
    """
    if output_path is None:
        output_path = RESULTS_DIR / "scaling_plot.pdf"
    
    try:
        # Load data
        df = load_scaling_data_from_csv(input_path)
        
        # Sort by agent_count for consistent plotting
        df = df.sort_values('agent_count')
        
        agent_counts = df['agent_count'].values
        spec_indices = df['specialization_index'].values
        retrieval_effs = df['retrieval_efficiency'].values
        
        # Fit power laws
        beta_spec, r2_spec = fit_power_law_safe(agent_counts, spec_indices)
        beta_ret, r2_ret = fit_power_law_safe(agent_counts, retrieval_effs)
        
        # Create figure with two subplots
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        
        # --- Specialization Index Plot ---
        ax1.scatter(agent_counts, spec_indices, color='blue', s=100, zorder=5, 
                   label='Observed', edgecolors='black')
        
        # Plot fitted curve
        if beta_spec is not None:
            x_fit = np.linspace(min(agent_counts), max(agent_counts), 100)
            y_fit = power_law(x_fit, beta_spec)
            ax1.plot(x_fit, y_fit, 'b--', linewidth=2, label=f'Power-law fit (β={beta_spec:.3f})')
            ax1.set_title(f'Specialization Index vs Agent Count\n(Exponent β = {beta_spec:.3f}, R² = {r2_spec:.3f})')
        else:
            ax1.set_title('Specialization Index vs Agent Count\n(Fit unavailable)')
        
        ax1.set_xlabel('Number of Agents')
        ax1.set_ylabel('Specialization Index')
        ax1.set_xticks(agent_counts)
        ax1.grid(True, alpha=0.3)
        ax1.legend(loc='best')
        
        # --- Retrieval Efficiency Plot ---
        ax2.scatter(agent_counts, retrieval_effs, color='green', s=100, zorder=5,
                   label='Observed', edgecolors='black')
        
        # Plot fitted curve
        if beta_ret is not None:
            x_fit = np.linspace(min(agent_counts), max(agent_counts), 100)
            y_fit = power_law(x_fit, beta_ret)
            ax2.plot(x_fit, y_fit, 'g--', linewidth=2, label=f'Power-law fit (β={beta_ret:.3f})')
            ax2.set_title(f'Retrieval Efficiency vs Agent Count\n(Exponent β = {beta_ret:.3f}, R² = {r2_ret:.3f})')
        else:
            ax2.set_title('Retrieval Efficiency vs Agent Count\n(Fit unavailable)')
        
        ax2.set_xlabel('Number of Agents')
        ax2.set_ylabel('Retrieval Efficiency')
        ax2.set_xticks(agent_counts)
        ax2.grid(True, alpha=0.3)
        ax2.legend(loc='best')
        
        # Add explicit note about 3 data points limitation
        note_text = (
            "NOTE: Power-law reliability is limited.\n"
            "Only 3 data points (N=3, 5, 7) available for fitting.\n"
            "Extrapolation beyond this range is not recommended."
        )
        
        # Place note at bottom center spanning both subplots
        fig.text(0.5, 0.02, note_text, 
                fontsize=10, ha='center', va='bottom',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        # Adjust layout to make room for note
        plt.tight_layout(rect=[0, 0.08, 1, 1])
        
        # Save to PDF
        plt.savefig(output_path, dpi=dpi, bbox_inches='tight')
        plt.close(fig)
        
        return ScalingPlotResult(
            success=True,
            output_path=output_path,
            exponent=beta_spec if beta_spec else beta_ret,
            r_squared=r2_spec if r2_spec else r2_ret,
            message=f"Plot saved to {output_path}"
        )
        
    except Exception as e:
        return ScalingPlotResult(
            success=False,
            output_path=output_path,
            exponent=None,
            r_squared=None,
            message=f"Failed to generate plot: {str(e)}"
        )


def build_parser() -> argparse.ArgumentParser:
    """Build command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="Generate scaling plot with power-law fits and reliability notes."
    )
    parser.add_argument(
        "--input", "-i",
        type=Path,
        default=None,
        help="Path to input scaling data CSV (default: results/scaling_data.csv)"
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=None,
        help="Path to output PDF file (default: results/scaling_plot.pdf)"
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=300,
        help="Resolution for output image (default: 300)"
    )
    return parser


def main(args: Optional[List[str]] = None) -> int:
    """Main entry point for scaling plot generation."""
    parser = build_parser()
    parsed_args = parser.parse_args(args)
    
    result = generate_scaling_plot_with_notes(
        input_path=parsed_args.input,
        output_path=parsed_args.output,
        dpi=parsed_args.dpi
    )
    
    if result.success:
        print(f"✓ {result.message}")
        print(f"  Exponent: {result.exponent}")
        print(f"  R-squared: {result.r_squared}")
        return 0
    else:
        print(f"✗ {result.message}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
