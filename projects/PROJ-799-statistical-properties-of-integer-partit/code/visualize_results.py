"""
Visualization module for statistical properties of integer partitions into distinct primes.

Generates plots comparing residual error R(n) against prime density and gap features.
Specifically addresses the hypothesis that prime gaps ('holes') drive deviations
from the asymptotic baseline.
"""

import os
import csv
import math
import argparse
from typing import List, Dict, Any, Optional, Tuple

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

# Ensure matplotlib uses a non-interactive backend for headless execution
import matplotlib
matplotlib.use('Agg')

# Import project utilities
# Note: We rely on the standard library and numpy for math operations here.
# If utils modules are needed, they should be imported explicitly if available.
# For this task, we assume the data files exist as per the pipeline flow.

def load_features(filepath: str) -> Dict[str, List[Any]]:
    """
    Load features from a CSV file into a dictionary of lists.
    Expects columns: n, R_n (residual), prime_gap_size, pi_n (count of primes <= n).
    """
    data = {
        'n': [],
        'R_n': [],
        'prime_gap_size': [],
        'pi_n': []
    }
    
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Feature file not found: {filepath}")

    with open(filepath, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data['n'].append(int(row['n']))
            # Handle potential float conversion for R_n
            try:
                data['R_n'].append(float(row['R_n']))
            except (ValueError, KeyError):
                # Fallback if column name differs or value is missing
                data['R_n'].append(0.0)
            
            try:
                data['prime_gap_size'].append(float(row['prime_gap_size']))
            except (ValueError, KeyError):
                data['prime_gap_size'].append(0.0)

            try:
                data['pi_n'].append(float(row['pi_n']))
            except (ValueError, KeyError):
                # If pi_n is missing, we might need to compute it or approximate.
                # For now, we assume it's present or we compute density as 0.
                data['pi_n'].append(0.0)

    return data

def compute_prime_density(n: int, pi_n: float) -> float:
    """
    Compute local prime density pi(n)/n.
    """
    if n == 0:
        return 0.0
    return pi_n / n

def plot_residual_vs_density(
    n_values: List[int],
    residuals: List[float],
    densities: List[float],
    gap_sizes: List[float],
    output_path: str,
    title: str = "Residual Error vs. Local Prime Density"
) -> None:
    """
    Create a dual-axis plot showing:
    1. Residual R(n) vs n (primary y-axis)
    2. Local Prime Density pi(n)/n vs n (secondary y-axis)
    
    Also overlays vertical lines at significant prime gaps if data allows.
    """
    if not n_values:
        raise ValueError("No data provided for plotting.")

    fig, ax1 = plt.subplots(figsize=(12, 8))

    # Primary Y-axis: Residuals
    color_res = 'tab:blue'
    ax1.set_xlabel('n (Integer)', fontsize=12)
    ax1.set_ylabel('Residual R(n) = log(p_P(n)) - log(Q_as(n))', color=color_res, fontsize=12)
    ax1.plot(n_values, residuals, color=color_res, linewidth=0.8, alpha=0.7, label='Residual R(n)')
    ax1.tick_params(axis='y', labelcolor=color_res)
    ax1.grid(True, which='both', linestyle='--', alpha=0.5)

    # Secondary Y-axis: Prime Density
    ax2 = ax1.twinx()
    color_density = 'tab:orange'
    ax2.set_ylabel('Local Prime Density π(n)/n', color=color_density, fontsize=12)
    ax2.plot(n_values, densities, color=color_density, linewidth=0.8, alpha=0.7, label='Density π(n)/n')
    ax2.tick_params(axis='y', labelcolor=color_density)
    
    # Combine legends
    lines_1, labels_1 = ax1.get_legend_handles_labels()
    lines_2, labels_2 = ax2.get_legend_handles_labels()
    ax1.legend(lines_1 + lines_2, labels_1 + labels_2, loc='upper right')

    # Optional: Highlight large gaps if data exists
    # We define a "large gap" as > 10% of the mean gap size in the dataset
    if gap_sizes and len(gap_sizes) > 10:
        mean_gap = np.mean(gap_sizes)
        threshold = mean_gap * 1.5
        large_gap_indices = [i for i, g in enumerate(gap_sizes) if g > threshold]
        
        for idx in large_gap_indices:
            n_val = n_values[idx]
            # Draw a vertical line for significant gaps
            ax1.axvline(x=n_val, color='gray', linestyle=':', linewidth=1, alpha=0.5)

    plt.title(title, fontsize=14)
    plt.tight_layout()

    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"Plot saved to: {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Visualize residuals against prime density.")
    parser.add_argument(
        "--input", 
        type=str, 
        default="data/processed/features.csv",
        help="Path to the features CSV file."
    )
    parser.add_argument(
        "--output", 
        type=str, 
        default="data/processed/residual_vs_density.png",
        help="Path to save the output plot."
    )
    args = parser.parse_args()

    try:
        data = load_features(args.input)
        
        if not data['n']:
            print("Error: No data loaded from features file.")
            return

        # Compute densities on the fly if not explicitly in data, 
        # but the task implies we use existing pi(n) or compute it.
        # Assuming 'pi_n' column exists from T016a feature engineering.
        densities = [compute_prime_density(n, pi) for n, pi in zip(data['n'], data['pi_n'])]

        plot_residual_vs_density(
            n_values=data['n'],
            residuals=data['R_n'],
            densities=densities,
            gap_sizes=data['prime_gap_size'],
            output_path=args.output,
            title="Residual Error R(n) vs. Local Prime Density π(n)/n"
        )

    except FileNotFoundError as e:
        print(f"Critical Error: {e}")
        print("Ensure that T016a (feature_engineering.py) has run successfully.")
        raise
    except Exception as e:
        print(f"Error during visualization: {e}")
        raise

if __name__ == "__main__":
    main()