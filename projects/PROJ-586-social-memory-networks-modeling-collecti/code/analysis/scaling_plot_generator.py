"""
Scaling Plot Generator for User Story 3.

Generates scaling_plot.pdf with fitted power-law curves and an explicit note
that 3 data points limit power-law reliability.

Produces: projects/PROJ-586-social-memory-networks-modeling-collecti/results/scaling_plot.pdf
"""
from __future__ import annotations

import argparse
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple, Optional

import numpy as np
import pandas as pd

# Import existing analysis utilities
try:
    from analysis.scaling import fit_power_law, load_scaling_data
except ImportError:
    # Fallback if running directly from code/
    sys.path.insert(0, str(Path(__file__).parent))
    from scaling import fit_power_law, load_scaling_data


@dataclass
class ScalingPlotResult:
    """Result of scaling plot generation."""
    output_path: str
    agent_counts: List[int]
    specialization_indices: List[float]
    retrieval_efficiencies: List[float]
    fitted_exponents: dict
    note: str


def power_law(x: float, a: float, b: float) -> float:
    """Power law function: y = a * x^b."""
    return a * (x ** b)


def fit_power_law_with_ci(
    x: np.ndarray,
    y: np.ndarray
) -> Tuple[float, float, float, float]:
    """
    Fit a power law y = a * x^b to data using log-log linear regression.
    
    Returns:
        Tuple of (a, b, a_std_err, b_std_err)
    """
    # Avoid log(0)
    mask = (x > 0) & (y > 0)
    if mask.sum() < 2:
        # Not enough points for fitting
        return 1.0, 0.0, 1.0, 1.0
    
    log_x = np.log(x[mask])
    log_y = np.log(y[mask])
    
    # Linear regression on log-log data
    # y = log(a) + b * log(x)
    n = len(log_x)
    sum_x = log_x.sum()
    sum_y = log_y.sum()
    sum_xx = (log_x ** 2).sum()
    sum_xy = (log_x * log_y).sum()
    
    # Slope (b) and intercept (log(a))
    denom = n * sum_xx - sum_x ** 2
    if abs(denom) < 1e-10:
        return 1.0, 0.0, 1.0, 1.0
        
    b = (n * sum_xy - sum_x * sum_y) / denom
    log_a = (sum_y - b * sum_x) / n
    a = math.exp(log_a)
    
    # Standard errors (simplified)
    # Residuals
    y_pred = log_a + b * log_x
    residuals = log_y - y_pred
    ss_res = (residuals ** 2).sum()
    ss_tot = ((log_y - log_y.mean()) ** 2).sum()
    
    # R-squared
    r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
    
    # Standard error of estimate
    s_err = math.sqrt(ss_res / (n - 2)) if n > 2 else 1.0
    
    # Standard errors of coefficients
    var_b = s_err ** 2 / (sum_xx - sum_x ** 2 / n)
    var_log_a = s_err ** 2 * sum_xx / (n * (sum_xx - sum_x ** 2 / n))
    
    std_b = math.sqrt(var_b) if var_b > 0 else 1.0
    std_log_a = math.sqrt(var_log_a) if var_log_a > 0 else 1.0
    std_a = a * std_log_a  # Delta method approximation
    
    return a, b, std_a, std_b


def load_scaling_data_real(data_path: Path) -> pd.DataFrame:
    """
    Load scaling data from CSV.
    
    Expected columns: agent_count, specialization_index, retrieval_efficiency
    """
    if not data_path.exists():
        raise FileNotFoundError(f"Scaling data file not found: {data_path}")
    
    df = pd.read_csv(data_path)
    required_cols = ['agent_count', 'specialization_index', 'retrieval_efficiency']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    
    return df


def generate_scaling_plot_with_notes(
    data_path: Path,
    output_path: Path
) -> ScalingPlotResult:
    """
    Generate scaling plot PDF with power-law fits and reliability note.
    
    Creates a PDF with:
    - Two subplots: Specialization Index vs Agent Count, Retrieval Efficiency vs Agent Count
    - Fitted power-law curves overlaid on data points
    - Explicit note: "3 data points limit power-law reliability"
    
    Args:
        data_path: Path to scaling data CSV
        output_path: Path to output PDF file
        
    Returns:
        ScalingPlotResult with metadata
    """
    # Load data
    df = load_scaling_data_real(data_path)
    
    agent_counts = df['agent_count'].values
    spec_indices = df['specialization_index'].values
    retrieval_effs = df['retrieval_efficiency'].values
    
    # Convert to numpy arrays
    x = np.array(agent_counts, dtype=float)
    y_spec = np.array(spec_indices, dtype=float)
    y_ret = np.array(retrieval_effs, dtype=float)
    
    # Fit power laws
    a_spec, b_spec, _, _ = fit_power_law_with_ci(x, y_spec)
    a_ret, b_ret, _, _ = fit_power_law_with_ci(x, y_ret)
    
    # Generate smooth curve for plotting
    x_smooth = np.linspace(x.min(), x.max(), 100)
    y_spec_fit = power_law(x_smooth, a_spec, b_spec)
    y_ret_fit = power_law(x_smooth, a_ret, b_ret)
    
    # Create plot using matplotlib
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    import matplotlib.pyplot as plt
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    
    # Plot 1: Specialization Index
    ax1.scatter(x, y_spec, s=100, c='blue', alpha=0.7, label='Measured')
    ax1.plot(x_smooth, y_spec_fit, 'b-', linewidth=2, 
             label=f'Power-law fit (exponent={b_spec:.3f})')
    ax1.set_xlabel('Number of Agents', fontsize=11)
    ax1.set_ylabel('Specialization Index', fontsize=11)
    ax1.set_title('Specialization Index vs Agent Count', fontsize=12)
    ax1.legend(loc='best')
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim(2, max(x) + 1)
    
    # Plot 2: Retrieval Efficiency
    ax2.scatter(x, y_ret, s=100, c='green', alpha=0.7, label='Measured')
    ax2.plot(x_smooth, y_ret_fit, 'g-', linewidth=2,
             label=f'Power-law fit (exponent={b_ret:.3f})')
    ax2.set_xlabel('Number of Agents', fontsize=11)
    ax2.set_ylabel('Retrieval Efficiency', fontsize=11)
    ax2.set_title('Retrieval Efficiency vs Agent Count', fontsize=12)
    ax2.legend(loc='best')
    ax2.grid(True, alpha=0.3)
    ax2.set_xlim(2, max(x) + 1)
    
    # Add explicit note about data point limitation
    note_text = "Note: 3 data points limit power-law reliability."
    fig.text(0.5, 0.02, note_text, 
             ha='center', va='bottom', fontsize=10,
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    plt.tight_layout(rect=[0, 0.08, 1, 1])
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save to PDF
    plt.savefig(output_path, dpi=150, format='pdf')
    plt.close(fig)
    
    return ScalingPlotResult(
        output_path=str(output_path),
        agent_counts=list(agent_counts),
        specialization_indices=list(spec_indices),
        retrieval_efficiencies=list(retrieval_effs),
        fitted_exponents={'specialization': b_spec, 'retrieval': b_ret},
        note=note_text
    )


def build_parser() -> argparse.ArgumentParser:
    """Build argument parser for scaling plot generation."""
    parser = argparse.ArgumentParser(
        description='Generate scaling plot with power-law fits and reliability note.'
    )
    parser.add_argument(
        '--data',
        type=str,
        default='data/scaling_results.csv',
        help='Path to scaling data CSV file'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='projects/PROJ-586-social-memory-networks-modeling-collecti/results/scaling_plot.pdf',
        help='Path to output PDF file'
    )
    return parser


def main():
    """Main entry point for scaling plot generation."""
    parser = build_parser()
    args = parser.parse_args()
    
    data_path = Path(args.data)
    output_path = Path(args.output)
    
    print(f"Loading scaling data from: {data_path}")
    print(f"Output plot to: {output_path}")
    
    try:
        result = generate_scaling_plot_with_notes(data_path, output_path)
        print(f"Successfully generated scaling plot: {result.output_path}")
        print(f"Fitted exponents: {result.fitted_exponents}")
        print(f"Note included: {result.note}")
        return 0
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        print("Make sure scaling data has been generated first (T027/T029).", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error generating plot: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
