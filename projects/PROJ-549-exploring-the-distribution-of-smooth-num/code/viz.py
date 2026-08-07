"""
Visualization module for smooth number density analysis.

Generates density vs. interval length plots with 95% confidence intervals
and theoretical curves for BOTH the Spec-defined and Plan-defined grids.

Outputs:
  - data/density_spec_grid.png
  - data/density_plan_grid.png
"""

import argparse
import logging
import os
import sys
from typing import Dict, List, Optional, Tuple, Any

import numpy as np
import matplotlib.pyplot as plt
from scipy import stats

# Local imports
from config import load_config
from dickman import rho, DickmanFunction
from analysis import load_density_data


def setup_logging(verbose: bool = False) -> None:
    """Configure logging for the visualization module."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )


def load_and_group_data(filepath: str, grid_type: str) -> Dict[str, List[Dict[str, Any]]]:
    """
    Load density data from CSV and group by y-value for plotting.

    Args:
        filepath: Path to the density measurements CSV.
        grid_type: 'spec' or 'plan' to determine column handling.

    Returns:
        Dictionary mapping y-values to lists of data points.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Data file not found: {filepath}. "
                                "Run T023 to generate density measurements first.")

    data = load_density_data(filepath)

    grouped: Dict[int, List[Dict[str, Any]]] = {}

    for row in data:
        y = int(row['y'])
        if y not in grouped:
            grouped[y] = []
        grouped[y].append(row)

    # Sort groups by y-value for consistent plotting
    return {k: grouped[k] for k in sorted(grouped.keys())}


def calculate_confidence_intervals(data_points: List[Dict[str, Any]]) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Calculate mean density and 95% confidence intervals for a group of data points.

    Args:
        data_points: List of dictionaries containing 'h' and 'density' keys.

    Returns:
        Tuple of (h_values, mean_density, ci_lower, ci_upper).
    """
    if not data_points:
        return np.array([]), np.array([]), np.array([]), np.array([])

    h_values = np.array([p['h'] for p in data_points])
    densities = np.array([p['density'] for p in data_points])

    # Sort by h for plotting
    sort_idx = np.argsort(h_values)
    h_values = h_values[sort_idx]
    densities = densities[sort_idx]

    # Calculate mean and standard error
    mean_density = np.mean(densities)
    std_density = np.std(densities, ddof=1) if len(densities) > 1 else 0
    n = len(densities)

    # 95% Confidence Interval
    if n > 1:
        se = std_density / np.sqrt(n)
        ci_margin = stats.t.ppf(0.975, n-1) * se
    else:
        se = 0
        ci_margin = 0

    return h_values, mean_density, mean_density - ci_margin, mean_density + ci_margin


def plot_spec_grid(grouped_data: Dict[int, List[Dict[str, Any]]], output_path: str) -> None:
    """
    Generate density vs. interval length plot for the Spec-defined grid.

    The Spec grid uses h = x^alpha, so we plot against the computed h values.
    Includes theoretical Dickman function curves.
    """
    plt.figure(figsize=(12, 8))

    # Colors for different y values
    colors = plt.cm.viridis(np.linspace(0, 1, len(grouped_data)))

    for idx, (y, points) in enumerate(grouped_data.items()):
        h_vals, mean_dens, ci_low, ci_high = calculate_confidence_intervals(points)

        if len(h_vals) == 0:
            continue

        # Plot confidence interval band
        plt.fill_between(h_vals, ci_low, ci_high, alpha=0.2, color=colors[idx],
                         label=f'y={y} (95% CI)' if idx == 0 else "")

        # Plot mean points
        plt.scatter(h_vals, [mean_dens] * len(h_vals), color=colors[idx], s=50, zorder=5)

        # Plot theoretical curve (Dickman function)
        # For Spec grid, we approximate theoretical density as rho(u) where u = log(x)/log(y)
        # Since x varies, we compute theoretical values at the observed h points
        theoretical_densities = []
        for p in points:
            x = p['x']
            u = np.log(x) / np.log(y) if y > 1 else np.inf
            theoretical_densities.append(rho(u))

        theoretical_densities = np.array(theoretical_densities)
        theoretical_h = np.array([p['h'] for p in points])

        # Sort theoretical by h for smooth line
        sort_idx = np.argsort(theoretical_h)
        theoretical_h = theoretical_h[sort_idx]
        theoretical_densities = theoretical_densities[sort_idx]

        plt.plot(theoretical_h, theoretical_densities, '--', color=colors[idx],
                 alpha=0.7, linewidth=1.5, label=f'y={y} (Theory)' if idx == 0 else "")

    plt.xscale('log')
    plt.yscale('log')
    plt.xlabel('Interval Length (h)', fontsize=12)
    plt.ylabel('Smooth Number Density (ρ)', fontsize=12)
    plt.title('Smooth Number Density vs. Interval Length (Spec Grid: h = x^α)',
              fontsize=14, fontweight='bold')
    plt.legend(loc='upper right', fontsize=10)
    plt.grid(True, alpha=0.3, which='both')
    plt.tight_layout()

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    logging.info(f"Spec grid plot saved to: {output_path}")


def plot_plan_grid(grouped_data: Dict[int, List[Dict[str, Any]]], output_path: str) -> None:
    """
    Generate density vs. interval length plot for the Plan-defined grid.

    The Plan grid uses fixed h values, making this a cleaner comparison.
    Includes theoretical Dickman function curves.
    """
    plt.figure(figsize=(12, 8))

    # Colors for different y values
    colors = plt.cm.plasma(np.linspace(0, 1, len(grouped_data)))

    for idx, (y, points) in enumerate(grouped_data.items()):
        h_vals, mean_dens, ci_low, ci_high = calculate_confidence_intervals(points)

        if len(h_vals) == 0:
            continue

        # Plot confidence interval band
        plt.fill_between(h_vals, ci_low, ci_high, alpha=0.2, color=colors[idx],
                         label=f'y={y} (95% CI)' if idx == 0 else "")

        # Plot mean points
        plt.scatter(h_vals, [mean_dens] * len(h_vals), color=colors[idx], s=50, zorder=5)

        # Plot theoretical curve
        theoretical_densities = []
        for p in points:
            x = p['x']
            u = np.log(x) / np.log(y) if y > 1 else np.inf
            theoretical_densities.append(rho(u))

        theoretical_densities = np.array(theoretical_densities)
        theoretical_h = np.array([p['h'] for p in points])

        # Sort theoretical by h for smooth line
        sort_idx = np.argsort(theoretical_h)
        theoretical_h = theoretical_h[sort_idx]
        theoretical_densities = theoretical_densities[sort_idx]

        plt.plot(theoretical_h, theoretical_densities, '--', color=colors[idx],
                 alpha=0.7, linewidth=1.5, label=f'y={y} (Theory)' if idx == 0 else "")

    plt.xscale('log')
    plt.yscale('log')
    plt.xlabel('Interval Length (h)', fontsize=12)
    plt.ylabel('Smooth Number Density (ρ)', fontsize=12)
    plt.title('Smooth Number Density vs. Interval Length (Plan Grid: Fixed h)',
              fontsize=14, fontweight='bold')
    plt.legend(loc='upper right', fontsize=10)
    plt.grid(True, alpha=0.3, which='both')
    plt.tight_layout()

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    logging.info(f"Plan grid plot saved to: {output_path}")


def main(args: Optional[argparse.Namespace] = None) -> int:
    """
    Main entry point for visualization generation.

    Generates two plots:
      1. Spec grid: density_measurements_spec.csv -> density_spec_grid.png
      2. Plan grid: density_measurements_plan.csv -> density_plan_grid.png
    """
    parser = argparse.ArgumentParser(
        description='Generate density vs. interval length plots for smooth number analysis.'
    )
    parser.add_argument('--config', type=str, default=None,
                        help='Path to configuration file (optional)')
    parser.add_argument('--spec-data', type=str, default='data/density_measurements_spec.csv',
                        help='Path to Spec grid density data')
    parser.add_argument('--plan-data', type=str, default='data/density_measurements_plan.csv',
                        help='Path to Plan grid density data')
    parser.add_argument('--output-dir', type=str, default='data',
                        help='Output directory for plots')
    parser.add_argument('--verbose', action='store_true',
                        help='Enable verbose logging')

    if args is None:
        args = parser.parse_args()

    setup_logging(args.verbose)

    # Load configuration if provided
    if args.config:
        try:
            config = load_config(args.config)
            logging.info(f"Loaded configuration from: {args.config}")
        except Exception as e:
            logging.warning(f"Could not load config: {e}. Using defaults.")

    # Generate Spec grid plot
    spec_output = os.path.join(args.output_dir, 'density_spec_grid.png')
    try:
        spec_data = load_and_group_data(args.spec_data, 'spec')
        plot_spec_grid(spec_data, spec_output)
    except FileNotFoundError as e:
        logging.error(f"Spec grid data missing: {e}")
        return 1
    except Exception as e:
        logging.error(f"Error generating Spec grid plot: {e}")
        return 1

    # Generate Plan grid plot
    plan_output = os.path.join(args.output_dir, 'density_plan_grid.png')
    try:
        plan_data = load_and_group_data(args.plan_data, 'plan')
        plot_plan_grid(plan_data, plan_output)
    except FileNotFoundError as e:
        logging.error(f"Plan grid data missing: {e}")
        return 1
    except Exception as e:
        logging.error(f"Error generating Plan grid plot: {e}")
        return 1

    logging.info("Visualization generation completed successfully.")
    return 0


if __name__ == '__main__':
    sys.exit(main())