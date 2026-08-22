"""
Visualization script for User Story 2: Phase Transition Threshold Detection.

Plots the probability of outlier emergence vs. perturbation strength (theta)
for different sparsity patterns, based on aggregated Monte Carlo results.

Output: data/figures/outlier_probability_vs_theta.png
"""

import os
import sys
import logging
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

# Ensure code directory is in path for imports
code_dir = Path(__file__).resolve().parent.parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from utils.config import get_project_paths, ensure_directories

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def sigmoid_function(x: np.ndarray, theta_c: float, slope: float) -> np.ndarray:
    """
    Logistic sigmoid function for fitting the phase transition.

    Parameters
    ----------
    x : np.ndarray
        Theta values.
    theta_c : float
        Critical threshold (inflection point).
    slope : float
        Steepness of the transition.

    Returns
    -------
    np.ndarray
        Probability values.
    """
    return 1.0 / (1.0 + np.exp(-slope * (x - theta_c)))

def load_aggregated_results() -> Dict[str, Any]:
    """
    Load aggregated Monte Carlo results from data/processed/threshold_sweep_results.csv.
    The file is expected to contain columns: N, theta, sparsity_pattern, outlier_count, total_runs, probability.

    Returns
    -------
    Dict[str, Any]
        Dictionary containing aggregated data grouped by sparsity pattern.
    """
    import csv

    results_path = get_project_paths()['processed_data'] / 'threshold_sweep_results.csv'

    if not results_path.exists():
        raise FileNotFoundError(
            f"Aggregated results file not found at {results_path}. "
            "Ensure T024 has been executed successfully."
        )

    data_by_pattern: Dict[str, Dict[str, List[float]]] = {}

    with open(results_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            pattern = row['sparsity_pattern']
            theta = float(row['theta'])
            prob = float(row['probability'])

            if pattern not in data_by_pattern:
                data_by_pattern[pattern] = {
                    'theta': [],
                    'probability': []
                }

            data_by_pattern[pattern]['theta'].append(theta)
            data_by_pattern[pattern]['probability'].append(prob)

    # Convert lists to numpy arrays and sort by theta
    for pattern in data_by_pattern:
        theta_arr = np.array(data_by_pattern[pattern]['theta'])
        prob_arr = np.array(data_by_pattern[pattern]['probability'])
        sorted_indices = np.argsort(theta_arr)
        data_by_pattern[pattern]['theta'] = theta_arr[sorted_indices]
        data_by_pattern[pattern]['probability'] = prob_arr[sorted_indices]

    return data_by_pattern

def plot_probability_vs_theta(
    data: Dict[str, Dict[str, np.ndarray]],
    output_path: Path,
    fit_curve: bool = True
) -> None:
    """
    Plot probability of outlier emergence vs. theta for different sparsity patterns.

    Parameters
    ----------
    data : Dict[str, Dict[str, np.ndarray]]
        Aggregated data grouped by sparsity pattern.
    output_path : Path
        Path to save the output plot.
    fit_curve : bool
        Whether to fit a sigmoid curve to the data points.
    """
    plt.figure(figsize=(10, 7))

    colors = ['blue', 'red', 'green', 'purple', 'orange', 'brown', 'pink', 'gray']
    markers = ['o', 's', '^', 'D', 'x', '+', '*', 'v']

    for idx, (pattern, pattern_data) in enumerate(data.items()):
        theta = pattern_data['theta']
        prob = pattern_data['probability']

        color = colors[idx % len(colors)]
        marker = markers[idx % len(markers)]

        plt.scatter(theta, prob, label=f'{pattern}', color=color, marker=marker, alpha=0.7, s=80)

        if fit_curve and len(theta) >= 3:
            try:
                # Initial guess for curve fitting: theta_c at median theta, slope = 5
                p0 = [np.median(theta), 5.0]
                popt, _ = curve_fit(sigmoid_function, theta, prob, p0=p0, maxfev=5000)
                theta_c, slope = popt

                theta_fit = np.linspace(min(theta), max(theta), 200)
                prob_fit = sigmoid_function(theta_fit, theta_c, slope)

                plt.plot(theta_fit, prob_fit, color=color, linestyle='--', alpha=0.5)

                logger.info(f"Fitted theta_c for {pattern}: {theta_c:.4f} (slope: {slope:.4f})")
            except Exception as e:
                logger.warning(f"Could not fit curve for {pattern}: {e}")

    plt.xlabel(r'Perturbation Strength $\theta$', fontsize=14)
    plt.ylabel('Probability of Outlier Emergence', fontsize=14)
    plt.title('Phase Transition: Outlier Probability vs. Perturbation Strength\nby Sparsity Pattern', fontsize=16)
    plt.legend(fontsize=12, loc='lower right')
    plt.grid(True, alpha=0.3)
    plt.xlim(left=0)  # Theta is non-negative
    plt.ylim(0, 1.05)

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    logger.info(f"Plot saved to {output_path}")

def main() -> None:
    """Main entry point for the visualization script."""
    logger.info("Starting outlier probability visualization...")

    try:
        # Load aggregated results
        data = load_aggregated_results()

        if not data:
            logger.error("No data found in aggregated results. Aborting.")
            sys.exit(1)

        logger.info(f"Loaded data for {len(data)} sparsity patterns: {list(data.keys())}")

        # Define output path
        output_path = get_project_paths()['figures'] / 'outlier_probability_vs_theta.png'

        # Generate plot
        plot_probability_vs_theta(data, output_path, fit_curve=True)

        logger.info("Visualization completed successfully.")

    except FileNotFoundError as e:
        logger.error(f"Data file missing: {e}")
        logger.error("Ensure T024 (threshold_sweep_results.csv generation) has been completed.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during visualization: {e}")
        raise

if __name__ == '__main__':
    main()