"""
Scaling analysis for User Story 3: Power-law fitting for metric trends vs. agent count.

This module implements power-law fitting for specialization index and retrieval efficiency
as a function of agent count (3, 5, 7 agents). It fits the model:
    y = a * N^b
where N is the number of agents, and returns the exponent b with confidence intervals.
"""
from __future__ import annotations

import pathlib
import warnings
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

# Import real metric computation functions from existing modules
from metrics.specialization import compute_specialization_index
from metrics.retrieval import compute_retrieval_efficiency


def power_law(N: np.ndarray, a: float, b: float) -> np.ndarray:
    """
    Power-law model: y = a * N^b

    Args:
        N: Number of agents (independent variable)
        a: Scaling coefficient
        b: Scaling exponent

    Returns:
        Predicted metric values
    """
    return a * np.power(N, b)


def fit_power_law(
    N: np.ndarray,
    y: np.ndarray,
    p0: Optional[Tuple[float, float]] = None
) -> Tuple[float, float]:
    """
    Fit a power-law model y = a * N^b to data using least squares.

    Args:
        N: Number of agents (independent variable)
        y: Metric values (dependent variable)
        p0: Initial guess for (a, b). If None, uses (1.0, 0.0).

    Returns:
        Tuple (a, b) of fitted parameters
    """
    from scipy.optimize import curve_fit

    if p0 is None:
        p0 = (1.0, 0.0)

    # Use log-log transformation for better numerical stability
    # log(y) = log(a) + b * log(N)
    log_N = np.log(N)
    log_y = np.log(y)

    # Linear regression in log-log space
    coeffs = np.polyfit(log_N, log_y, 1)
    b = coeffs[0]
    log_a = coeffs[1]
    a = np.exp(log_a)

    return a, b


def fit_power_law_with_ci(
    N: np.ndarray,
    y: np.ndarray,
    n_boot: int = 1000,
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Fit power-law model with bootstrap confidence intervals.

    Args:
        N: Number of agents (independent variable)
        y: Metric values (dependent variable)
        n_boot: Number of bootstrap iterations
        alpha: Significance level for confidence intervals

    Returns:
        Dictionary with:
            - 'a': fitted coefficient
            - 'b': fitted exponent
            - 'b_ci': (lower, upper) confidence interval for exponent
            - 'r_squared': R^2 of the fit
    """
    from scipy.optimize import curve_fit

    # Initial fit
    a, b = fit_power_law(N, y)

    # Bootstrap for confidence intervals
    b_samples = []
    for _ in range(n_boot):
        # Resample with replacement
        indices = np.random.choice(len(N), size=len(N), replace=True)
        N_boot = N[indices]
        y_boot = y[indices]

        try:
            a_boot, b_boot = fit_power_law(N_boot, y_boot)
            b_samples.append(b_boot)
        except Exception:
            continue

    if len(b_samples) == 0:
        b_ci = (b, b)
    else:
        b_samples = np.array(b_samples)
        lower = np.percentile(b_samples, 100 * alpha / 2)
        upper = np.percentile(b_samples, 100 * (1 - alpha / 2))
        b_ci = (lower, upper)

    # Compute R^2
    y_pred = power_law(N, a, b)
    ss_res = np.sum((y - y_pred) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

    return {
        'a': a,
        'b': b,
        'b_ci': b_ci,
        'r_squared': r_squared
    }


def load_scaling_data(
    data_path: str = "data/scaling_results.csv"
) -> pd.DataFrame:
    """
    Load scaling experiment results from CSV.

    Expected columns: agent_count, specialization_index, retrieval_efficiency

    Args:
        data_path: Path to CSV file with scaling results

    Returns:
        DataFrame with scaling data
    """
    path = pathlib.Path(data_path)
    if not path.exists():
        raise FileNotFoundError(f"Scaling data file not found: {data_path}")

    df = pd.read_csv(path)

    # Ensure required columns exist
    required_cols = ['agent_count', 'specialization_index', 'retrieval_efficiency']
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")

    return df


def generate_scaling_plot(
    data_path: str = "data/scaling_results.csv",
    output_path: str = "results/scaling_plot.pdf",
    note_on_3pts: bool = True
) -> Dict[str, Any]:
    """
    Generate scaling plot with power-law fits and confidence intervals.

    Args:
        data_path: Path to scaling results CSV
        output_path: Path for output PDF plot
        note_on_3pts: Whether to add note about 3-point limitation

    Returns:
        Dictionary with fit results for each metric
    """
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    import matplotlib.pyplot as plt

    # Load data
    df = load_scaling_data(data_path)

    # Group by agent count and compute mean metrics
    aggregated = df.groupby('agent_count').agg({
        'specialization_index': 'mean',
        'retrieval_efficiency': 'mean'
    }).reset_index()

    N = aggregated['agent_count'].values.astype(float)
    spec_mean = aggregated['specialization_index'].values
    ret_mean = aggregated['retrieval_efficiency'].values

    # Fit power laws
    spec_fit = fit_power_law_with_ci(N, spec_mean)
    ret_fit = fit_power_law_with_ci(N, ret_mean)

    # Create plot
    fig, ax = plt.subplots(figsize=(10, 6))

    # Plot specialization index
    N_plot = np.linspace(N.min(), N.max(), 100)
    ax.scatter(N, spec_mean, color='blue', label='Specialization Index (mean)', zorder=5)
    ax.plot(N_plot, power_law(N_plot, spec_fit['a'], spec_fit['b']),
            color='blue', linestyle='-', linewidth=2,
            label=f'Specialization fit: y = {spec_fit["a"]:.3f} * N^{spec_fit["b"]:.3f}')

    # Plot retrieval efficiency
    ax.scatter(N, ret_mean, color='red', label='Retrieval Efficiency (mean)', zorder=5)
    ax.plot(N_plot, power_law(N_plot, ret_fit['a'], ret_fit['b']),
            color='red', linestyle='--', linewidth=2,
            label=f'Retrieval fit: y = {ret_fit["a"]:.3f} * N^{ret_fit["b"]:.3f}')

    # Add confidence interval shading for specialization
    N_ci = np.linspace(N.min(), N.max(), 100)
    spec_lower = power_law(N_ci, spec_fit['a'], spec_fit['b_ci'][0])
    spec_upper = power_law(N_ci, spec_fit['a'], spec_fit['b_ci'][1])
    ax.fill_between(N_ci, spec_lower, spec_upper, color='blue', alpha=0.2)

    # Labels and legend
    ax.set_xlabel('Number of Agents (N)', fontsize=12)
    ax.set_ylabel('Metric Value', fontsize=12)
    ax.set_title('Scaling of Collective Remembering Metrics with Agent Count', fontsize=14)
    ax.legend(loc='best', fontsize=10)
    ax.grid(True, alpha=0.3)

    # Add note about 3-point limitation if requested
    if note_on_3pts:
        note_text = "Note: Only 3 data points (N=3,5,7). Power-law reliability is limited."
        ax.text(0.5, 0.02, note_text, transform=ax.transAxes,
                fontsize=9, ha='center', va='bottom',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    plt.tight_layout()

    # Ensure output directory exists
    output_dir = pathlib.Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save plot
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()

    return {
        'specialization': spec_fit,
        'retrieval': ret_fit,
        'n_points': len(N),
        'output_path': str(output_path)
    }


def main() -> None:
    """
    Main entry point for scaling analysis.
    Loads scaling data, fits power laws, and generates the plot.
    """
    import argparse

    parser = argparse.ArgumentParser(
        description='Scaling analysis: power-law fitting for metric trends vs. agent count'
    )
    parser.add_argument(
        '--data',
        type=str,
        default='data/scaling_results.csv',
        help='Path to scaling results CSV'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='results/scaling_plot.pdf',
        help='Path for output PDF plot'
    )
    parser.add_argument(
        '--no-note',
        action='store_true',
        help='Do not add note about 3-point limitation'
    )

    args = parser.parse_args()

    print(f"Loading scaling data from: {args.data}")
    result = generate_scaling_plot(
        data_path=args.data,
        output_path=args.output,
        note_on_3pts=not args.no_note
    )

    print(f"Generated plot: {result['output_path']}")
    print(f"Specialization exponent (b): {result['specialization']['b']:.4f} "
          f"CI: [{result['specialization']['b_ci'][0]:.4f}, "
          f"{result['specialization']['b_ci'][1]:.4f}]")
    print(f"Retrieval exponent (b): {result['retrieval']['b']:.4f} "
          f"CI: [{result['retrieval']['b_ci'][0]:.4f}, "
          f"{result['retrieval']['b_ci'][1]:.4f}]")
    print(f"R^2 (specialization): {result['specialization']['r_squared']:.4f}")
    print(f"R^2 (retrieval): {result['retrieval']['r_squared']:.4f}")


if __name__ == '__main__':
    main()