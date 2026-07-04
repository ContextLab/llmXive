"""
Scaling plot generator for User Story 3.

Generates scaling_plot.pdf with fitted power-law curves and an explicit note
that 3 data points limit power-law reliability.

This module loads real scaling data from code/data/generate_scaling_data.py,
fits a power-law model, and produces a PDF plot with appropriate warnings.
"""
from __future__ import annotations

import argparse
import math
import sys
import warnings
from pathlib import Path
from typing import List, Optional, Tuple

import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for CI
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Import real data generator
from data.generate_scaling_data import run_scaling_simulation


def power_law(x: np.ndarray, a: float, b: float) -> np.ndarray:
    """Power law function: y = a * x^b."""
    return a * np.power(x, b)


def fit_power_law_with_ci(
    x: np.ndarray, y: np.ndarray
) -> Tuple[float, float, float, float]:
    """
    Fit a power law y = a * x^b using log-log linear regression.
    
    Returns:
        Tuple of (a, b, a_95ci_low, b_95ci_low) - coefficients and lower CI bounds.
        Note: With only 3 points, CI is extremely wide and should be interpreted
        with caution.
    """
    if len(x) < 2:
        raise ValueError("Need at least 2 points to fit a power law.")
    
    # Log-transform
    log_x = np.log(x)
    log_y = np.log(y)
    
    # Linear regression on log-log data
    # y = a * x^b  =>  log(y) = log(a) + b * log(x)
    # Let A = log(a), B = b
    # log(y) = A + B * log(x)
    
    n = len(x)
    sum_x = np.sum(log_x)
    sum_y = np.sum(log_y)
    sum_xy = np.sum(log_x * log_y)
    sum_xx = np.sum(log_x ** 2)
    
    # Slope (B) and intercept (A)
    denom = n * sum_xx - sum_x ** 2
    if abs(denom) < 1e-10:
        raise ValueError("Singular matrix in regression; points may be collinear.")
    
    B = (n * sum_xy - sum_x * sum_y) / denom
    A = (sum_y - B * sum_x) / n
    
    # Standard error of estimate
    y_pred = A + B * log_x
    residuals = log_y - y_pred
    sse = np.sum(residuals ** 2)
    mse = sse / (n - 2) if n > 2 else sse
    se_estimate = math.sqrt(mse) if n > 2 else 0.0
    
    # Standard errors of coefficients
    se_B = se_estimate / math.sqrt(sum_xx - sum_x ** 2 / n) if (sum_xx - sum_x ** 2 / n) > 0 else 0.0
    se_A = se_estimate * math.sqrt(sum_xx / denom) if denom > 0 else 0.0
    
    # 95% CI using t-distribution (df = n-2)
    # For n=3, df=1, t_0.975 = 12.706 (very wide CI!)
    # For n=5, df=3, t_0.975 = 3.182
    # For n=7, df=5, t_0.975 = 2.571
    if n > 2:
        # Approximate t-values for common df
        t_vals = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 
                 6: 2.447, 7: 2.365, 8: 2.306, 9: 2.262, 10: 2.228}
        df = n - 2
        t_crit = t_vals.get(df, 2.0)  # Default to 2.0 if df not in table
    else:
        t_crit = 2.0  # Minimum reasonable value
    
    ci_B = t_crit * se_B
    ci_A = t_crit * se_A
    
    # Convert back to original scale
    a = math.exp(A)
    b = B
    a_ci_low = math.exp(A - ci_A)
    b_ci_low = B - ci_B
    
    return a, b, a_ci_low, b_ci_low


def load_scaling_data_real(data_path: Path) -> pd.DataFrame:
    """
    Load scaling data from a CSV file.
    
    If the file doesn't exist, run the simulation to generate it.
    Returns DataFrame with columns: agent_count, specialization_index, retrieval_efficiency
    """
    if data_path.exists():
        df = pd.read_csv(data_path)
        return df
    
    # Generate data if not present
    print(f"Scaling data not found at {data_path}, generating...")
    run_scaling_simulation(
        agent_counts=[3, 5, 7],
        games_per_count=100,  # Reduced for speed
        output_path=data_path
    )
    df = pd.read_csv(data_path)
    return df


def generate_scaling_plot_with_notes(
    data_path: Path,
    output_path: Path,
    agent_counts: List[int] = [3, 5, 7],
    games_per_count: int = 100
) -> None:
    """
    Generate scaling_plot.pdf with fitted power-law curves and explicit note
    about 3 data points limiting reliability.
    
    The plot includes:
    1. Specialization index vs. agent count with power-law fit
    2. Retrieval efficiency vs. agent count with power-law fit
    3. Explicit annotation: "Note: 3 data points limit power-law reliability"
    """
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Load or generate data
    df = load_scaling_data_real(data_path)
    
    if len(df) < 3:
        raise ValueError(
            f"Need at least 3 data points for scaling analysis. "
            f"Found {len(df)}. Run generate_scaling_data.py first."
        )
    
    # Filter to requested agent counts
    df = df[df['agent_count'].isin(agent_counts)].sort_values('agent_count')
    
    if len(df) < 3:
        raise ValueError(
            f"After filtering, need at least 3 data points. "
            f"Found {len(df)}."
        )
    
    x = np.array(df['agent_count'].values, dtype=float)
    y_spec = np.array(df['specialization_index'].values, dtype=float)
    y_ret = np.array(df['retrieval_efficiency'].values, dtype=float)
    
    # Fit power laws
    try:
        a_spec, b_spec, _, _ = fit_power_law_with_ci(x, y_spec)
        a_ret, b_ret, _, _ = fit_power_law_with_ci(x, y_ret)
    except ValueError as e:
        raise RuntimeError(f"Power law fitting failed: {e}")
    
    # Create plot
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # Specialization index plot
    ax1.scatter(x, y_spec, s=100, zorder=3, label='Observed', color='tab:blue')
    x_fit = np.linspace(min(x), max(x), 100)
    y_spec_fit = power_law(x_fit, a_spec, b_spec)
    ax1.plot(x_fit, y_spec_fit, 'b--', linewidth=2, label=f'Power-law fit: y = {a_spec:.3f}·x^{b_spec:.3f}')
    ax1.set_xlabel('Number of Agents (N)', fontsize=12)
    ax1.set_ylabel('Specialization Index', fontsize=12)
    ax1.set_title('Specialization vs. Agent Count', fontsize=14)
    ax1.legend(loc='best')
    ax1.grid(True, alpha=0.3)
    ax1.set_xscale('log')
    ax1.set_yscale('log')
    
    # Retrieval efficiency plot
    ax2.scatter(x, y_ret, s=100, zorder=3, label='Observed', color='tab:orange')
    y_ret_fit = power_law(x_fit, a_ret, b_ret)
    ax2.plot(x_fit, y_ret_fit, 'orange--', linewidth=2, label=f'Power-law fit: y = {a_ret:.3f}·x^{b_ret:.3f}')
    ax2.set_xlabel('Number of Agents (N)', fontsize=12)
    ax2.set_ylabel('Retrieval Efficiency', fontsize=12)
    ax2.set_title('Retrieval Efficiency vs. Agent Count', fontsize=14)
    ax2.legend(loc='best')
    ax2.grid(True, alpha=0.3)
    ax2.set_xscale('log')
    ax2.set_yscale('log')
    
    # Add explicit note about 3 data points limitation
    note_text = (
        "Note: 3 data points limit power-law reliability.\n"
        "Confidence intervals are extremely wide (t-critical ≈ 12.7 for df=1).\n"
        "Results should be interpreted as preliminary."
    )
    fig.text(
        0.5, 0.02, 
        note_text, 
        ha='center', 
        va='bottom', 
        fontsize=10,
        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5)
    )
    
    plt.tight_layout(rect=[0, 0.08, 1, 1])
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"Scaling plot saved to {output_path}")
    print(f"  Specialization fit: y = {a_spec:.4f} * x^{b_spec:.4f}")
    print(f"  Retrieval fit:      y = {a_ret:.4f} * x^{b_ret:.4f}")
    print(f"  WARNING: Only {len(df)} data points; power-law fit is preliminary.")


def build_parser() -> argparse.ArgumentParser:
    """Build argument parser for the scaling plot generator."""
    parser = argparse.ArgumentParser(
        description='Generate scaling plot with power-law fits and reliability notes.'
    )
    parser.add_argument(
        '--data',
        type=str,
        default='data/scaling_results.csv',
        help='Path to scaling data CSV (default: data/scaling_results.csv)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='results/scaling_plot.pdf',
        help='Output PDF path (default: results/scaling_plot.pdf)'
    )
    parser.add_argument(
        '--agent-counts',
        type=str,
        default='3,5,7',
        help='Comma-separated agent counts to include (default: 3,5,7)'
    )
    parser.add_argument(
        '--games',
        type=int,
        default=100,
        help='Games per agent count if regenerating data (default: 100)'
    )
    return parser


def main() -> int:
    """Main entry point."""
    parser = build_parser()
    args = parser.parse_args()
    
    data_path = Path(args.data)
    output_path = Path(args.output)
    agent_counts = [int(x) for x in args.agent_counts.split(',')]
    
    try:
        generate_scaling_plot_with_notes(
            data_path=data_path,
            output_path=output_path,
            agent_counts=agent_counts,
            games_per_count=args.games
        )
        return 0
    except Exception as e:
        print(f"Error generating scaling plot: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())