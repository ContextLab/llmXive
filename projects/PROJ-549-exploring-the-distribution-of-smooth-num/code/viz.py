"""
Visualization module for smooth number distribution analysis.

This module generates plots for density measurements across Spec-defined and
Plan-defined parameter grids. It includes confidence intervals and theoretical
curves for comparison.

IMPORTANT: This analysis measures statistical associations. Correlation does not
imply causation. The trends observed are descriptive of the data within the
sampled intervals and do not establish causal mechanisms.
"""

import argparse
import logging
import os
import sys
from typing import Dict, List, Optional, Tuple, Any

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.ticker import ScalarFormatter, LogFormatter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def setup_logging() -> logging.Logger:
    """Configure and return the module logger."""
    return logger


def load_and_group_data(
    file_path: str,
    group_by: List[str] = ['y']
) -> Dict[str, pd.DataFrame]:
    """
    Load density measurement data from CSV and group by specified columns.

    Args:
        file_path: Path to the CSV file containing density measurements.
        group_by: List of column names to group data by.

    Returns:
        Dictionary mapping group keys to DataFrames.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Data file not found: {file_path}")

    logger.info(f"Loading data from {file_path}")
    df = pd.read_csv(file_path)

    # Ensure numeric columns are properly typed
    numeric_cols = ['x', 'y', 'h', 'density', 'dickman_rho', 'deviation_ratio']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    grouped = {}
    if group_by:
        for name, group in df.groupby(group_by):
            key = tuple(name) if isinstance(name, tuple) else (name,)
            grouped[key] = group
    else:
        grouped[('all',)] = df

    logger.info(f"Loaded data with {len(df)} rows, grouped into {len(grouped)} groups")
    return grouped


def calculate_confidence_intervals(
    df: pd.DataFrame,
    confidence_level: float = 0.95
) -> Tuple[pd.Series, pd.Series]:
    """
    Calculate confidence intervals for density measurements.

    Args:
        df: DataFrame containing density measurements.
        confidence_level: Confidence level for intervals (default 0.95).

    Returns:
        Tuple of (lower_bound, upper_bound) Series.
    """
    if len(df) < 2:
        # Single point: return the point itself
        return df['density'], df['density']

    mean_density = df['density'].mean()
    std_density = df['density'].std()
    n = len(df)

    # t-distribution for small samples, normal for large
    if n > 30:
        z_score = 1.96  # Approximate for 95%
    else:
        from scipy import stats
        z_score = stats.t.ppf(1 - (1 - confidence_level) / 2, df=n-1)

    margin = z_score * (std_density / np.sqrt(n))

    lower = mean_density - margin
    upper = mean_density + margin

    return pd.Series([lower] * len(df), index=df.index), \
           pd.Series([upper] * len(df), index=df.index)


def plot_spec_grid(
    data_path: str,
    output_path: str,
    y_values: List[int],
    title: str = "Density vs Interval Length (Spec Grid)",
    annotation_text: str = "Associational Trend Only"
) -> None:
    """
    Plot density measurements for the Spec-defined parameter grid.

    Args:
        data_path: Path to the CSV file with Spec grid results.
        output_path: Path to save the plot.
        y_values: List of y values to plot.
        title: Plot title.
        annotation_text: Text to annotate on the plot.
    """
    logger.info(f"Generating Spec grid plot: {output_path}")

    try:
        grouped = load_and_group_data(data_path, group_by=['y', 'x'])
    except FileNotFoundError as e:
        logger.error(f"Cannot generate plot: {e}")
        return

    fig, ax = plt.subplots(figsize=(12, 8))

    colors = plt.cm.viridis(np.linspace(0, 0.8, len(y_values)))

    for idx, y_val in enumerate(y_values):
        # Filter data for this y value
        y_data = None
        for key, df in grouped.items():
            if key[0] == y_val:
                y_data = df
                break

        if y_data is None or y_data.empty:
            logger.warning(f"No data found for y={y_val}")
            continue

        # Group by h to aggregate multiple x values
        h_grouped = y_data.groupby('h').agg({
            'density': ['mean', 'std', 'count']
        }).reset_index()
        h_grouped.columns = ['h', 'mean_density', 'std_density', 'count']

        # Sort by h
        h_grouped = h_grouped.sort_values('h')

        # Calculate confidence intervals
        lower, upper = calculate_confidence_intervals(h_grouped)

        # Plot
        ax.errorbar(
            h_grouped['h'],
            h_grouped['mean_density'],
            yerr=[
                h_grouped['mean_density'] - lower,
                upper - h_grouped['mean_density']
            ],
            capsize=5,
            label=f'y={y_val}',
            color=colors[idx],
            marker='o',
            linestyle='-'
        )

    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_xlabel('Interval Length (h)', fontsize=12)
    ax.set_ylabel('Smooth Number Density (ρ)', fontsize=12)
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.legend(loc='best', fontsize=10)
    ax.grid(True, which='both', linestyle='--', alpha=0.7)

    # Add annotation per Spec Assumptions
    ax.annotate(
        annotation_text,
        xy=(0.05, 0.95),
        xycoords='axes fraction',
        fontsize=9,
        verticalalignment='top',
        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5),
        fontfamily='monospace'
    )

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    logger.info(f"Spec grid plot saved to {output_path}")


def plot_plan_grid(
    data_path: str,
    output_path: str,
    y_values: List[int],
    title: str = "Deviation Ratio vs Interval Length (Plan Grid)",
    annotation_text: str = "Associational Trend Only"
) -> None:
    """
    Plot deviation ratio measurements for the Plan-defined parameter grid.

    Args:
        data_path: Path to the CSV file with Plan grid results.
        output_path: Path to save the plot.
        y_values: List of y values to plot.
        title: Plot title.
        annotation_text: Text to annotate on the plot.
    """
    logger.info(f"Generating Plan grid plot: {output_path}")

    try:
        grouped = load_and_group_data(data_path, group_by=['y', 'x'])
    except FileNotFoundError as e:
        logger.error(f"Cannot generate plot: {e}")
        return

    fig, ax = plt.subplots(figsize=(12, 8))

    colors = plt.cm.plasma(np.linspace(0, 0.8, len(y_values)))

    for idx, y_val in enumerate(y_values):
        # Filter data for this y value
        y_data = None
        for key, df in grouped.items():
            if key[0] == y_val:
                y_data = df
                break

        if y_data is None or y_data.empty:
            logger.warning(f"No data found for y={y_val}")
            continue

        # Group by h to aggregate multiple x values
        h_grouped = y_data.groupby('h').agg({
            'deviation_ratio': ['mean', 'std', 'count']
        }).reset_index()
        h_grouped.columns = ['h', 'mean_ratio', 'std_ratio', 'count']

        # Sort by h
        h_grouped = h_grouped.sort_values('h')

        # Calculate confidence intervals
        lower, upper = calculate_confidence_intervals(h_grouped)

        # Plot
        ax.errorbar(
            h_grouped['h'],
            h_grouped['mean_ratio'],
            yerr=[
                h_grouped['mean_ratio'] - lower,
                upper - h_grouped['mean_ratio']
            ],
            capsize=5,
            label=f'y={y_val}',
            color=colors[idx],
            marker='s',
            linestyle='--'
        )

    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_xlabel('Interval Length (h)', fontsize=12)
    ax.set_ylabel('Deviation Ratio (R = ρ_obs / ρ_Dickman)', fontsize=12)
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.legend(loc='best', fontsize=10)
    ax.grid(True, which='both', linestyle='--', alpha=0.7)

    # Add annotation per Spec Assumptions
    ax.annotate(
        annotation_text,
        xy=(0.05, 0.95),
        xycoords='axes fraction',
        fontsize=9,
        verticalalignment='top',
        bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.5),
        fontfamily='monospace'
    )

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    logger.info(f"Plan grid plot saved to {output_path}")


def main() -> None:
    """Main entry point for visualization generation."""
    parser = argparse.ArgumentParser(
        description='Generate visualization plots for smooth number density analysis.'
    )
    parser.add_argument(
        '--spec-data',
        type=str,
        default='data/density_measurements_spec.csv',
        help='Path to Spec grid data CSV'
    )
    parser.add_argument(
        '--plan-data',
        type=str,
        default='data/density_measurements_plan.csv',
        help='Path to Plan grid data CSV'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='data',
        help='Output directory for plots'
    )
    parser.add_argument(
        '--y-values',
        type=int,
        nargs='+',
        default=[100, 1000, 10000],
        help='Y values to plot'
    )
    parser.add_argument(
        '--spec-output',
        type=str,
        default='density_spec_grid.png',
        help='Output filename for Spec grid plot'
    )
    parser.add_argument(
        '--plan-output',
        type=str,
        default='deviation_plan_grid.png',
        help='Output filename for Plan grid plot'
    )

    args = parser.parse_args()

    # Ensure output directory exists
    os.makedirs(args.output_dir, exist_ok=True)

    # Generate Spec grid plot
    spec_path = os.path.join(args.output_dir, args.spec_output)
    plot_spec_grid(
        args.spec_data,
        spec_path,
        args.y_values,
        annotation_text="Associational Trend Only"
    )

    # Generate Plan grid plot
    plan_path = os.path.join(args.output_dir, args.plan_output)
    plot_plan_grid(
        args.plan_data,
        plan_path,
        args.y_values,
        annotation_text="Associational Trend Only"
    )

    logger.info("Visualization generation complete")


if __name__ == '__main__':
    main()
