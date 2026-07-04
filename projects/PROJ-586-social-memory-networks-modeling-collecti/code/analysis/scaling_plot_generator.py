"""
Scaling Plot Generator for Social Memory Networks.

Generates scaling_plot.pdf with fitted power-law curves and explicit notes
about the limitations of 3 data points for power-law reliability.
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
matplotlib.use('Agg')  # Non-interactive backend for CI/CI-like environments
import matplotlib.pyplot as plt

# Import from existing analysis modules
from analysis.scaling import fit_power_law, load_scaling_data


@dataclass
class ScalingPlotResult:
    """Result of the scaling plot generation."""
    output_path: Path
    fitted_exponent: Optional[float]
    fitted_coefficient: Optional[float]
    r_squared: Optional[float]
    note_added: bool


def power_law(x: np.ndarray, a: float, b: float) -> np.ndarray:
    """Compute power law: y = a * x^b."""
    return a * np.power(x, b)


def fit_power_law_with_ci(
    x: np.ndarray,
    y: np.ndarray,
    confidence: float = 0.95
) -> Tuple[float, float, float, Optional[float], Optional[float]]:
    """
    Fit a power law to data and return coefficient, exponent, R-squared,
    and confidence intervals for the exponent.
    
    Returns:
        (a, b, r_squared, ci_lower, ci_upper)
    """
    # Avoid log(0) or log(negative)
    valid_mask = (x > 0) & (y > 0)
    if not np.any(valid_mask):
        return 0.0, 0.0, 0.0, None, None

    x_valid = x[valid_mask]
    y_valid = y[valid_mask]

    # Log-transform for linear regression: log(y) = log(a) + b * log(x)
    log_x = np.log(x_valid)
    log_y = np.log(y_valid)

    # Linear regression
    n = len(log_x)
    if n < 2:
        return 0.0, 0.0, 0.0, None, None

    mean_log_x = np.mean(log_x)
    mean_log_y = np.mean(log_y)

    # Slope (b) and intercept (log_a)
    numerator = np.sum((log_x - mean_log_x) * (log_y - mean_log_y))
    denominator = np.sum((log_x - mean_log_x) ** 2)

    if denominator == 0:
        return 0.0, 0.0, 0.0, None, None

    b = numerator / denominator
    log_a = mean_log_y - b * mean_log_x
    a = np.exp(log_a)

    # R-squared
    y_pred = log_a + b * log_x
    ss_res = np.sum((log_y - y_pred) ** 2)
    ss_tot = np.sum((log_y - mean_log_y) ** 2)
    r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

    # Confidence interval for b (exponent)
    # Standard error of the slope
    if n > 2:
        residual_std = np.sqrt(ss_res / (n - 2))
        se_b = residual_std / np.sqrt(denominator)
        # t-value for 95% CI with n-2 degrees of freedom
        from scipy import stats
        t_val = stats.t.ppf((1 + confidence) / 2, df=n - 2)
        ci_lower = b - t_val * se_b
        ci_upper = b + t_val * se_b
    else:
        ci_lower = None
        ci_upper = None

    return a, b, r_squared, ci_lower, ci_upper


def load_scaling_data_real(data_path: Path) -> pd.DataFrame:
    """
    Load scaling data from CSV file.
    
    Expected columns: agent_count, specialization_index, retrieval_efficiency
    """
    if not data_path.exists():
        raise FileNotFoundError(f"Scaling data file not found: {data_path}")
    
    df = pd.read_csv(data_path)
    
    # Ensure required columns exist
    required_cols = ['agent_count', 'specialization_index', 'retrieval_efficiency']
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")
    
    return df


def generate_scaling_plot_with_notes(
    input_path: Path,
    output_path: Path,
    note_text: str = "Note: 3 data points limit power-law reliability"
) -> ScalingPlotResult:
    """
    Generate scaling plot with power-law fits and explicit reliability notes.
    
    Args:
        input_path: Path to CSV with scaling data
        output_path: Path for output PDF
        note_text: Text to display in the plot about data limitations
    
    Returns:
        ScalingPlotResult with fit parameters and output path
    """
    # Load data
    df = load_scaling_data_real(input_path)
    
    # Sort by agent count
    df = df.sort_values('agent_count')
    
    agent_counts = df['agent_count'].values
    spec_indices = df['specialization_index'].values
    retrieval_effs = df['retrieval_efficiency'].values
    
    # Convert to numpy arrays
    x = np.array(agent_counts, dtype=float)
    y_spec = np.array(spec_indices, dtype=float)
    y_ret = np.array(retrieval_effs, dtype=float)
    
    # Fit power laws
    a_spec, b_spec, r2_spec, ci_spec_lower, ci_spec_upper = fit_power_law_with_ci(x, y_spec)
    a_ret, b_ret, r2_ret, ci_ret_lower, ci_ret_upper = fit_power_law_with_ci(x, y_ret)
    
    # Create figure with two subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # Plot 1: Specialization Index
    ax1.scatter(x, y_spec, color='blue', s=100, zorder=3, label='Measured')
    
    # Generate smooth curve for power law fit
    if b_spec != 0:
        x_smooth = np.linspace(min(x), max(x), 100)
        y_smooth = power_law(x_smooth, a_spec, b_spec)
        ax1.plot(x_smooth, y_smooth, 'b-', linewidth=2, 
                label=f'Power law fit (β={b_spec:.3f})')
    
    ax1.set_xlabel('Number of Agents (N)', fontsize=12)
    ax1.set_ylabel('Specialization Index', fontsize=12)
    ax1.set_title('Specialization Index vs. Agent Count', fontsize=14)
    ax1.grid(True, alpha=0.3)
    ax1.legend(loc='best')
    
    # Plot 2: Retrieval Efficiency
    ax2.scatter(x, y_ret, color='green', s=100, zorder=3, label='Measured')
    
    if b_ret != 0:
        x_smooth = np.linspace(min(x), max(x), 100)
        y_smooth = power_law(x_smooth, a_ret, b_ret)
        ax2.plot(x_smooth, y_smooth, 'g-', linewidth=2,
                label=f'Power law fit (β={b_ret:.3f})')
    
    ax2.set_xlabel('Number of Agents (N)', fontsize=12)
    ax2.set_ylabel('Retrieval Efficiency', fontsize=12)
    ax2.set_title('Retrieval Efficiency vs. Agent Count', fontsize=14)
    ax2.grid(True, alpha=0.3)
    ax2.legend(loc='best')
    
    # Add reliability note to both plots
    fig.text(0.5, 0.02, note_text, 
            ha='center', va='bottom', fontsize=10, 
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    # Adjust layout to make room for the note
    plt.tight_layout(rect=[0, 0.08, 1, 1])
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save to PDF
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    return ScalingPlotResult(
        output_path=output_path,
        fitted_exponent=b_spec,  # Using specialization as primary metric
        fitted_coefficient=a_spec,
        r_squared=r2_spec,
        note_added=True
    )


def build_parser() -> argparse.ArgumentParser:
    """Build argument parser for the scaling plot generator."""
    parser = argparse.ArgumentParser(
        description='Generate scaling plot with power-law fits and reliability notes'
    )
    parser.add_argument(
        '--input', '-i',
        type=Path,
        required=True,
        help='Path to input CSV with scaling data'
    )
    parser.add_argument(
        '--output', '-o',
        type=Path,
        required=True,
        help='Path for output PDF'
    )
    parser.add_argument(
        '--note', '-n',
        type=str,
        default="Note: 3 data points limit power-law reliability",
        help='Custom note text for the plot'
    )
    return parser


def main() -> int:
    """Main entry point for the scaling plot generator."""
    parser = build_parser()
    args = parser.parse_args()
    
    try:
        result = generate_scaling_plot_with_notes(
            input_path=args.input,
            output_path=args.output,
            note_text=args.note
        )
        
        print(f"Scaling plot generated: {result.output_path}")
        if result.fitted_exponent is not None:
            print(f"Fitted exponent (β): {result.fitted_exponent:.4f}")
        if result.r_squared is not None:
            print(f"R-squared: {result.r_squared:.4f}")
        
        return 0
        
    except Exception as e:
        print(f"Error generating scaling plot: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())