"""
Visualization script for T025: Plot probability of outlier emergence vs. theta.

This script aggregates Monte Carlo results to calculate the empirical probability
of outlier emergence for each perturbation strength (theta) and sparsity pattern,
then generates a visualization saving the plot to data/figures/outlier_probability_vs_theta.png.

It relies on the aggregated results from T024 (threshold_sweep_results.csv) or
the Monte Carlo results from T021a (mc_results.csv) if the sweep aggregation is not present.
Given T024 is a prerequisite, this script primarily reads from data/processed/threshold_sweep_results.csv.
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

# Add project root to path for imports
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root / "code"))

from utils.config import get_project_paths, ensure_directories
from utils.logging_config import setup_simulation_logger

# Configure logging
logger = setup_simulation_logger(__name__, "plot_outlier_probability")

def sigmoid_function(x, a, b, c):
    """
    Sigmoid function for fitting the transition probability.
    P(outlier) = 1 / (1 + exp(-a * (x - c)))
    Where:
      a: steepness
      c: inflection point (theta_c)
      b: not strictly needed if we normalize, but kept for flexibility
    """
    # Ensure numerical stability
    return 1.0 / (1.0 + np.exp(-a * (x - c)))

def load_aggregated_results(input_path: Path) -> Dict[str, Any]:
    """
    Loads the aggregated results from the threshold sweep.
    Expected CSV schema (from T024):
    theta, N, sparsity_pattern, total_runs, outlier_count, outlier_probability
    """
    import csv

    if not input_path.exists():
        raise FileNotFoundError(f"Aggregated results file not found: {input_path}")

    data = {}
    with open(input_path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            theta = float(row["theta"])
            pattern = row["sparsity_pattern"]
            N = int(row["N"]) # Assuming N is constant or we group by it if needed

            # Group by (theta, pattern)
            key = (theta, pattern)
            if key not in data:
                data[key] = {
                    "theta": theta,
                    "pattern": pattern,
                    "total_runs": int(row["total_runs"]),
                    "outlier_count": int(row["outlier_count"]),
                    "probability": float(row["outlier_probability"])
                }

    return data

def plot_probability_vs_theta(
    data: Dict[Tuple[float, str], Dict[str, Any]],
    output_path: Path,
    figure_size: Tuple[int, int] = (10, 6)
) -> None:
    """
    Plots the probability of outlier emergence vs. theta for different sparsity patterns.
    Fits a sigmoid curve to each pattern to highlight the critical threshold.
    """
    ensure_directories([output_path.parent])

    # Group data by pattern
    patterns = {}
    for (theta, pattern), stats in data.items():
        if pattern not in patterns:
            patterns[pattern] = {"thetas": [], "probs": [], "counts": []}
        patterns[pattern]["thetas"].append(theta)
        patterns[pattern]["probs"].append(stats["probability"])
        patterns[pattern]["counts"].append(stats["outlier_count"])

    # Sort by theta for plotting
    for pattern in patterns:
        sorted_items = sorted(zip(patterns[pattern]["thetas"], patterns[pattern]["probs"]), key=lambda x: x[0])
        patterns[pattern]["thetas"] = [x[0] for x in sorted_items]
        patterns[pattern]["probs"] = [x[1] for x in sorted_items]

    plt.figure(figsize=figure_size)
    colors = plt.cm.tab10(np.linspace(0, 1, len(patterns)))

    for idx, (pattern, stats) in enumerate(patterns.items()):
        thetas = np.array(stats["thetas"])
        probs = np.array(stats["probs"])

        # Plot empirical points
        plt.scatter(thetas, probs, label=f"{pattern} (empirical)", alpha=0.7, s=50, color=colors[idx])

        # Fit sigmoid if we have enough points
        if len(thetas) >= 3:
            try:
                # Initial guess: steepness=1, center=2.0 (BBP threshold)
                popt, _ = curve_fit(
                    sigmoid_function, thetas, probs,
                    p0=[1.0, 2.0],
                    maxfev=5000,
                    bounds=([0, 1.0], [10, 4.0])
                )
                a_fit, c_fit = popt
                theta_fit = np.linspace(thetas.min(), thetas.max(), 100)
                prob_fit = sigmoid_function(theta_fit, a_fit, c_fit)
                plt.plot(theta_fit, prob_fit, linestyle="--", color=colors[idx], alpha=0.8,
                         label=f"{pattern} fit (θc≈{c_fit:.2f})")
            except Exception as e:
                logger.warning(f"Could not fit sigmoid for pattern {pattern}: {e}")

    plt.xlabel(r"Perturbation Strength $\theta$", fontsize=12)
    plt.ylabel("Probability of Outlier Emergence", fontsize=12)
    plt.title(r"Phase Transition: Outlier Probability vs. $\theta$ by Sparsity Pattern", fontsize=14)
    plt.legend(loc="best", fontsize=10)
    plt.grid(True, which="both", ls="-", alpha=0.3)
    plt.xlim(left=0) # Theta is non-negative

    # Save figure
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()

    logger.info(f"Visualization saved to {output_path}")

def main():
    """
    Main entry point for the visualization script.
    """
    paths = get_project_paths()
    input_file = paths["processed"] / "threshold_sweep_results.csv"
    output_file = paths["figures"] / "outlier_probability_vs_theta.png"

    logger.info(f"Starting outlier probability visualization task (T025)")
    logger.info(f"Reading aggregated results from: {input_file}")
    logger.info(f"Target output: {output_file}")

    try:
        # Load data
        data = load_aggregated_results(input_file)

        if not data:
            raise ValueError("No data found in the aggregated results file.")

        logger.info(f"Loaded {len(data)} data points across {len(set(k[1] for k in data.keys()))} sparsity patterns.")

        # Generate plot
        plot_probability_vs_theta(data, output_file)

        logger.info("Task T025 completed successfully.")
        return 0

    except FileNotFoundError as e:
        logger.error(f"Input file missing: {e}")
        logger.error("Ensure T024 (threshold_sweep_results.csv) has been executed successfully before running this task.")
        return 1
    except Exception as e:
        logger.error(f"Error during visualization generation: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())