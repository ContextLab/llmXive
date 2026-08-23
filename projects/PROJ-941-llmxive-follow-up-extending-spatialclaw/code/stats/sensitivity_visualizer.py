"""
T066: Implement Sensitivity Analysis Visualization.

Generates a plot in results/analysis/sensitivity_analysis_plot.png showing the variation
in false-positive and false-negative rates across tested threshold values.
This combines data from T031 (depth threshold sweep) and T058 (flat object epsilon sweep).
"""
import os
import sys
import csv
import json
import logging
import argparse
from typing import List, Dict, Any, Optional, Tuple

import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for server environments
import matplotlib.pyplot as plt
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Paths
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RESULTS_DIR = os.path.join(PROJECT_ROOT, 'results', 'analysis')
DEPTH_SWEEP_FILE = os.path.join(RESULTS_DIR, 'depth_threshold_sweep.csv')
FLAT_SWEEP_FILE = os.path.join(RESULTS_DIR, 'flat_object_sensitivity.csv')
OUTPUT_PLOT = os.path.join(RESULTS_DIR, 'sensitivity_analysis_plot.png')

def load_depth_sweep_data(filepath: str) -> Tuple[List[float], List[float], List[float]]:
    """
    Load depth threshold sweep data from T031.
    Returns: (thresholds, fpr, fnr)
    """
    if not os.path.exists(filepath):
        logger.warning(f"Depth sweep file not found: {filepath}. Skipping depth curve.")
        return [], [], []

    thresholds = []
    fpr = []
    fnr = []

    try:
        with open(filepath, 'r', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                thresholds.append(float(row['threshold_value']))
                fpr.append(float(row['false_positive_rate']))
                fnr.append(float(row['false_negative_rate']))
        logger.info(f"Loaded {len(thresholds)} points from depth sweep.")
    except Exception as e:
        logger.error(f"Error reading depth sweep file: {e}")
        return [], [], []

    return thresholds, fpr, fnr

def load_flat_sweep_data(filepath: str) -> Tuple[List[float], List[float], List[float]]:
    """
    Load flat object epsilon sweep data from T058.
    Returns: (epsilons, fpr, fnr)
    """
    if not os.path.exists(filepath):
        logger.warning(f"Flat sweep file not found: {filepath}. Skipping flat curve.")
        return [], [], []

    epsilons = []
    fpr = []
    fnr = []

    try:
        with open(filepath, 'r', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                epsilons.append(float(row['epsilon']))
                fpr.append(float(row['false_positive_rate']))
                fnr.append(float(row['false_negative_rate']))
        logger.info(f"Loaded {len(epsilons)} points from flat sweep.")
    except Exception as e:
        logger.error(f"Error reading flat sweep file: {e}")
        return [], [], []

    return epsilons, fpr, fnr

def generate_plot(
    depth_thresholds: List[float],
    depth_fpr: List[float],
    depth_fnr: List[float],
    flat_epsilons: List[float],
    flat_fpr: List[float],
    flat_fnr: List[float]
) -> None:
    """
    Generate the sensitivity analysis plot.
    Shows FPR and FNR curves for both depth and flat object thresholds.
    Highlights the 'elbow' or stability region.
    """
    fig, ax = plt.subplots(figsize=(12, 8))

    # Plot Depth Threshold Sweep (T031)
    if depth_thresholds:
        ax.plot(depth_thresholds, depth_fpr, 'b-o', label='Depth FPR', linewidth=2, markersize=8)
        ax.plot(depth_thresholds, depth_fnr, 'b--s', label='Depth FNR', linewidth=2, markersize=8, alpha=0.7)
        # Highlight stability region (approximate elbow)
        if len(depth_thresholds) > 1:
            # Simple heuristic: find where slope changes significantly
            slopes = np.diff(depth_fpr)
            if len(slopes) > 0:
                max_slope_idx = np.argmax(np.abs(slopes))
                elbow_x = depth_thresholds[max_slope_idx]
                ax.axvline(x=elbow_x, color='blue', linestyle=':', alpha=0.5, label=f'Depth Stability ~{elbow_x:.2f}m')

    # Plot Flat Object Sweep (T058)
    if flat_epsilons:
        ax.plot(flat_epsilons, flat_fpr, 'r-o', label='Flat FPR', linewidth=2, markersize=8, markerfacecolor='none')
        ax.plot(flat_epsilons, flat_fnr, 'r--s', label='Flat FNR', linewidth=2, markersize=8, markerfacecolor='none', alpha=0.7)
        # Highlight stability region for flat
        if len(flat_epsilons) > 1:
            slopes = np.diff(flat_fpr)
            if len(slopes) > 0:
                max_slope_idx = np.argmax(np.abs(slopes))
                elbow_x = flat_epsilons[max_slope_idx]
                ax.axvline(x=elbow_x, color='red', linestyle=':', alpha=0.5, label=f'Flat Stability ~{elbow_x:.3f}')

    # Formatting
    ax.set_xlabel('Threshold Value (meters / epsilon)', fontsize=12)
    ax.set_ylabel('Error Rate (FPR / FNR)', fontsize=12)
    ax.set_title('Sensitivity Analysis: Error Rates vs Threshold Values\n(T031 Depth Sweep & T058 Flat Object Sweep)', fontsize=14)
    ax.legend(loc='upper right', fontsize=10)
    ax.grid(True, linestyle='--', alpha=0.7)
    ax.set_ylim(-0.05, 1.05)
    ax.set_xlim(min(min(depth_thresholds) if depth_thresholds else 0, min(flat_epsilons) if flat_epsilons else 0) - 0.1,
                max(max(depth_thresholds) if depth_thresholds else 1, max(flat_epsilons) if flat_epsilons else 0) + 0.1)

    plt.tight_layout()

    # Ensure output directory exists
    os.makedirs(os.path.dirname(OUTPUT_PLOT), exist_ok=True)

    plt.savefig(OUTPUT_PLOT, dpi=150, bbox_inches='tight')
    logger.info(f"Plot saved to {OUTPUT_PLOT}")
    plt.close(fig)

def main():
    """Main entry point for T066."""
    parser = argparse.ArgumentParser(description='Generate Sensitivity Analysis Visualization (T066)')
    parser.add_argument('--depth-file', type=str, default=DEPTH_SWEEP_FILE, help='Path to depth threshold sweep CSV')
    parser.add_argument('--flat-file', type=str, default=FLAT_SWEEP_FILE, help='Path to flat object sensitivity CSV')
    parser.add_argument('--output', type=str, default=OUTPUT_PLOT, help='Output plot path')
    args = parser.parse_args()

    logger.info("Starting Sensitivity Analysis Visualization (T066)...")

    # Load data
    d_thresh, d_fpr, d_fnr = load_depth_sweep_data(args.depth_file)
    f_eps, f_fpr, f_fnr = load_flat_sweep_data(args.flat_file)

    if not d_thresh and not f_eps:
        logger.error("No data found to plot. Both input files are missing or empty.")
        sys.exit(1)

    # Generate plot
    generate_plot(d_thresh, d_fpr, d_fnr, f_eps, f_fpr, f_fnr)

    logger.info("T066 Sensitivity Analysis Visualization completed successfully.")

if __name__ == '__main__':
    main()
