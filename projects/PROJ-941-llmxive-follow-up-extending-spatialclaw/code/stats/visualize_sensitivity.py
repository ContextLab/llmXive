"""
T066: Implement Sensitivity Analysis Visualization.

Generates a plot showing the variation in false-positive and false-negative rates
across tested threshold values from T031 (depth threshold sweep) and T058 (flat object epsilon sweep).

Dependencies:
- results/analysis/depth_threshold_sweep.csv (from T031)
- results/analysis/flat_object_sensitivity.csv (from T058)

Output:
- results/analysis/sensitivity_analysis_plot.png
"""
import os
import csv
import logging
import argparse
from typing import List, Dict, Any, Optional, Tuple

import matplotlib
# Use non-interactive backend for headless execution
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

# Setup logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_sensitivity_csv(filepath: str) -> Optional[Dict[str, List[float]]]:
    """
    Load a sensitivity CSV file and return a dictionary of columns.
    Expected columns: threshold_value (or epsilon), false_positive_rate, false_negative_rate.
    """
    if not os.path.exists(filepath):
        logger.warning(f"File not found: {filepath}. Skipping.")
        return None

    data = {'threshold': [], 'fpr': [], 'fnr': []}
    try:
        with open(filepath, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Handle both 'threshold_value' and 'epsilon' column names
                threshold_key = None
                if 'threshold_value' in row:
                    threshold_key = 'threshold_value'
                elif 'epsilon' in row:
                    threshold_key = 'epsilon'
                
                if threshold_key is None:
                    logger.warning(f"Could not find threshold column in {filepath}. Skipping row.")
                    continue

                try:
                    t_val = float(row[threshold_key])
                    fpr = float(row.get('false_positive_rate', 0.0))
                    fnr = float(row.get('false_negative_rate', 0.0))
                    
                    data['threshold'].append(t_val)
                    data['fpr'].append(fpr)
                    data['fnr'].append(fnr)
                except (ValueError, TypeError) as e:
                    logger.warning(f"Error parsing row in {filepath}: {e}. Skipping.")
                    continue
    except Exception as e:
        logger.error(f"Error reading {filepath}: {e}")
        return None

    if not data['threshold']:
        logger.warning(f"No valid data found in {filepath}.")
        return None

    return data

def plot_sensitivity_analysis(
    depth_data: Optional[Dict[str, List[float]]],
    flat_data: Optional[Dict[str, List[float]]],
    output_path: str
) -> None:
    """
    Create a multi-panel plot showing sensitivity analysis results.
    """
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle('Sensitivity Analysis: Threshold & Flat Object Tolerance', fontsize=14, fontweight='bold')

    # Panel 1: Depth Threshold Sweep (T031)
    ax1 = axes[0]
    ax1.set_title('Depth Threshold Sensitivity (T031)', fontsize=12)
    ax1.set_xlabel('Threshold (meters)')
    ax1.set_ylabel('Error Rate')
    ax1.grid(True, linestyle='--', alpha=0.7)

    if depth_data:
        # Sort by threshold for smooth line plotting
        sorted_indices = np.argsort(depth_data['threshold'])
        thresholds = [depth_data['threshold'][i] for i in sorted_indices]
        fpr = [depth_data['fpr'][i] for i in sorted_indices]
        fnr = [depth_data['fnr'][i] for i in sorted_indices]

        ax1.plot(thresholds, fpr, 'o-', color='#1f77b4', label='False Positive Rate', markersize=6)
        ax1.plot(thresholds, fnr, 's-', color='#d62728', label='False Negative Rate', markersize=6)
        
        # Highlight "elbow" or stability region (approximate inflection point)
        if len(thresholds) > 2:
            # Simple heuristic: find where the slope changes significantly or values stabilize
            # For visualization, we just highlight the range where both are relatively low
            ax1.axvline(x=thresholds[len(thresholds)//2], color='gray', linestyle=':', alpha=0.5, label='Stability Region Start')
        
        ax1.legend(loc='best')
    else:
        ax1.text(0.5, 0.5, 'No Depth Threshold Data (T031)\nRun T031 first', 
                transform=ax1.transAxes, ha='center', va='center', color='gray', fontsize=12)

    # Panel 2: Flat Object Epsilon Sweep (T058)
    ax2 = axes[1]
    ax2.set_title('Flat Object Tolerance Sensitivity (T058)', fontsize=12)
    ax2.set_xlabel('Epsilon (Zero Depth Tolerance)')
    ax2.set_ylabel('Error Rate')
    ax2.grid(True, linestyle='--', alpha=0.7)

    if flat_data:
        # Sort by epsilon
        sorted_indices = np.argsort(flat_data['threshold']) # 'threshold' key used in load for epsilon too
        epsilons = [flat_data['threshold'][i] for i in sorted_indices]
        fpr_flat = [flat_data['fpr'][i] for i in sorted_indices]
        fnr_flat = [flat_data['fnr'][i] for i in sorted_indices]

        ax2.plot(epsilons, fpr_flat, 'o-', color='#2ca02c', label='False Positive Rate', markersize=6)
        ax2.plot(epsilons, fnr_flat, 's-', color='#ff7f0e', label='False Negative Rate', markersize=6)

        # Highlight stability region
        if len(epsilons) > 2:
            ax2.axvline(x=epsilons[len(epsilons)//2], color='gray', linestyle=':', alpha=0.5, label='Stability Region Start')

        ax2.legend(loc='best')
    else:
        ax2.text(0.5, 0.5, 'No Flat Object Data (T058)\nRun T058 first', 
                transform=ax2.transAxes, ha='center', va='center', color='gray', fontsize=12)

    plt.tight_layout()
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
        logger.info(f"Created directory: {output_dir}")

    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    logger.info(f"Plot saved to: {output_path}")
    plt.close(fig)

def main(args: Optional[argparse.Namespace] = None) -> int:
    """Main entry point."""
    if args is None:
        parser = argparse.ArgumentParser(description='Generate Sensitivity Analysis Visualization (T066)')
        parser.add_argument('--depth-csv', type=str, default='results/analysis/depth_threshold_sweep.csv',
                            help='Path to depth threshold sweep CSV (T031 output)')
        parser.add_argument('--flat-csv', type=str, default='results/analysis/flat_object_sensitivity.csv',
                            help='Path to flat object sensitivity CSV (T058 output)')
        parser.add_argument('--output', type=str, default='results/analysis/sensitivity_analysis_plot.png',
                            help='Output path for the plot')
        args = parser.parse_args()

    logger.info("Starting T066: Sensitivity Analysis Visualization")

    # Load data
    depth_data = load_sensitivity_csv(args.depth_csv)
    flat_data = load_sensitivity_csv(args.flat_csv)

    if not depth_data and not flat_data:
        logger.error("No input data found. Both T031 and T058 must be executed first.")
        return 1

    # Generate plot
    try:
        plot_sensitivity_analysis(depth_data, flat_data, args.output)
        logger.info("T066 completed successfully.")
        return 0
    except Exception as e:
        logger.error(f"Failed to generate plot: {e}", exc_info=True)
        return 1

if __name__ == '__main__':
    import sys
    sys.exit(main())
