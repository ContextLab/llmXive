"""
Scaling Plot Generation for Social Memory Networks.

Generates a PDF plot showing Specialization Index and Retrieval Efficiency
versus Agent Count, with fitted power-law curves and an explicit note about
the limitation of having only 3 data points.

This module implements T030.
"""
from __future__ import annotations

import argparse
import math
import sys
import warnings
from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np
import pandas as pd

# Ensure matplotlib uses a non-interactive backend for headless execution
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

# Import project utilities if available, otherwise define minimal fallbacks
try:
    from utils.logging import get_logger
except ImportError:
    # Fallback logger for standalone execution
    class _SimpleLogger:
        def info(self, msg, *args, **kwargs): print(f"[INFO] {msg % args if args else msg}")
        def warning(self, msg, *args, **kwargs): print(f"[WARNING] {msg % args if args else msg}")
        def error(self, msg, *args, **kwargs): print(f"[ERROR] {msg % args if args else msg}")
    def get_logger(name=None): return _SimpleLogger()

logger = get_logger(__name__)


def power_law(x: np.ndarray, a: float, b: float) -> np.ndarray:
    """Power-law function: y = a * x^b."""
    return a * np.power(x, b)


def fit_power_law(
    x: np.ndarray, y: np.ndarray
) -> Tuple[Optional[Tuple[float, float]], Optional[float]]:
    """
    Fit a power-law model y = a * x^b to the data.

    Returns:
        Tuple of (params (a, b), r_squared) or (None, None) if fit fails.
    """
    if len(x) < 2:
        logger.warning("Insufficient data points for power-law fitting.")
        return None, None

    # Filter out non-positive values for log-transform stability
    mask = (x > 0) & (y > 0)
    if np.sum(mask) < 2:
        logger.warning("Not enough positive data points for log-transform fitting.")
        return None, None

    x_fit = x[mask]
    y_fit = y[mask]

    try:
        # Linearize: log(y) = log(a) + b * log(x)
        log_x = np.log(x_fit)
        log_y = np.log(y_fit)

        # Perform linear regression
        coeffs = np.polyfit(log_x, log_y, 1)
        b = coeffs[0]
        log_a = coeffs[1]
        a = np.exp(log_a)

        # Calculate R-squared
        y_pred = a * np.power(x_fit, b)
        ss_res = np.sum((y_fit - y_pred) ** 2)
        ss_tot = np.sum((y_fit - np.mean(y_fit)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

        return (a, b), r_squared
    except Exception as e:
        logger.warning(f"Power-law fitting failed: {e}")
        return None, None


def load_scaling_data_real(
    data_path: Path,
) -> pd.DataFrame:
    """
    Load scaling data from a CSV file.

    Expected columns: 'agent_count', 'specialization_index', 'retrieval_efficiency'.
    """
    if not data_path.exists():
        raise FileNotFoundError(f"Scaling data file not found: {data_path}")

    df = pd.read_csv(data_path)
    required_cols = {'agent_count', 'specialization_index', 'retrieval_efficiency'}
    if not required_cols.issubset(df.columns):
        missing = required_cols - set(df.columns)
        raise ValueError(f"Missing required columns in {data_path}: {missing}")

    # Sort by agent_count for consistent plotting
    df = df.sort_values('agent_count').reset_index(drop=True)
    return df


def generate_scaling_plot_with_notes(
    df: pd.DataFrame,
    output_path: Path,
    title: str = "Scaling of Collective Remembering Metrics",
) -> None:
    """
    Generate a PDF plot with fitted power-law curves and a reliability note.

    The plot includes:
    1. Scatter points for Specialization Index and Retrieval Efficiency vs Agent Count.
    2. Fitted power-law curves (if possible).
    3. An explicit note stating that 3 data points limit power-law reliability.
    """
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    agent_counts = df['agent_count'].values.astype(float)
    spec_indices = df['specialization_index'].values.astype(float)
    retrieval_effs = df['retrieval_efficiency'].values.astype(float)

    fig, ax = plt.subplots(figsize=(10, 6))

    # Plot Specialization Index
    ax.scatter(agent_counts, spec_indices, color='blue', label='Specialization Index', zorder=3)
    # Plot Retrieval Efficiency
    ax.scatter(agent_counts, retrieval_effs, color='green', label='Retrieval Efficiency', zorder=3)

    # Fit and plot curves
    fit_params_spec, r2_spec = fit_power_law(agent_counts, spec_indices)
    fit_params_ret, r2_ret = fit_power_law(agent_counts, retrieval_effs)

    x_line = np.linspace(agent_counts.min(), agent_counts.max(), 100)

    if fit_params_spec:
        a, b = fit_params_spec
        y_line = a * np.power(x_line, b)
        ax.plot(x_line, y_line, 'b--', label=f'Spec Fit (R²={r2_spec:.2f})', zorder=2)
        logger.info(f"Specialization fit: y = {a:.4f} * x^{b:.4f}, R²={r2_spec:.4f}")
    else:
        logger.warning("Could not fit power law for Specialization Index.")

    if fit_params_ret:
        a, b = fit_params_ret
        y_line = a * np.power(x_line, b)
        ax.plot(x_line, y_line, 'g--', label=f'Retrieval Fit (R²={r2_ret:.2f})', zorder=2)
        logger.info(f"Retrieval fit: y = {a:.4f} * x^{b:.4f}, R²={r2_ret:.4f}")
    else:
        logger.warning("Could not fit power law for Retrieval Efficiency.")

    # Labels and Title
    ax.set_xlabel('Number of Agents', fontsize=12)
    ax.set_ylabel('Metric Value', fontsize=12)
    ax.set_title(title, fontsize=14)
    ax.legend(loc='best')
    ax.grid(True, linestyle=':', alpha=0.6)

    # Add the explicit reliability note as requested by T030
    note_text = (
        "Note: The scaling plot includes an explicit note that "
        "3 data points limit power-law reliability."
    )
    # Add text box inside the plot area
    props = dict(boxstyle='round', facecolor='wheat', alpha=0.8)
    ax.text(
        0.02, 0.98, note_text,
        transform=ax.transAxes,
        fontsize=10,
        verticalalignment='top',
        bbox=props
    )

    # Save to PDF
    plt.tight_layout()
    plt.savefig(output_path, format='pdf')
    plt.close()
    logger.info(f"Scaling plot saved to {output_path}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate scaling plot from experiment results."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data/scaling_results.csv"),
        help="Path to the scaling results CSV file.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/scaling_plot.pdf"),
        help="Path to save the output PDF.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    logger.info(f"Loading data from {args.input}")
    try:
        df = load_scaling_data_real(args.input)
    except (FileNotFoundError, ValueError) as e:
        logger.error(f"Failed to load data: {e}")
        return 1

    logger.info(f"Generating plot to {args.output}")
    try:
        generate_scaling_plot_with_notes(df, args.output)
    except Exception as e:
        logger.error(f"Failed to generate plot: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())