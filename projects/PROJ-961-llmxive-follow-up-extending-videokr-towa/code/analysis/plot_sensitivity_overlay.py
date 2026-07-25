"""
Plot sensitivity overlay: accuracy curves for different threshold definitions.

This script generates a plot overlaying accuracy vs. hop count curves for
different threshold definitions (2, 3, 4 hops) to visualize the stability
of the "reasoning cliff" detection.

Output: data/processed/sensitivity_overlay.png
"""

import csv
import json
import logging
import os
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple

import matplotlib.pyplot as plt
import numpy as np

from utils.config import get_project_root, get_path, ensure_dir

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_sensitivity_results() -> List[Dict]:
    """Load sensitivity analysis results from CSV."""
    csv_path = get_path("data/processed/sensitivity_thresholds.csv")
    if not csv_path.exists():
        raise FileNotFoundError(f"Sensitivity results not found: {csv_path}")

    results = []
    with open(csv_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            results.append({
                'threshold_hop': int(row['threshold_hop']),
                'p_value': float(row['p_value']),
                'effect_size': float(row['effect_size']),
                'is_significant': row['is_significant'].lower() == 'true'
            })
    return results


def load_annotated_data() -> List[Dict]:
    """Load annotated dataset with chain_length and correctness."""
    csv_path = get_path("data/processed/annotated_videokr.csv")
    if not csv_path.exists():
        raise FileNotFoundError(f"Annotated data not found: {csv_path}")

    data = []
    with open(csv_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append({
                'chain_length': int(row['chain_length']),
                'correctness': row['correctness'].lower() == 'true'
            })
    return data


def calculate_accuracy_by_hop(
    data: List[Dict],
    threshold_hop: int
) -> Dict[int, Tuple[float, int]]:
    """
    Calculate accuracy by hop count for a given threshold definition.

    For each hop count, compute the accuracy rate and sample count.
    The threshold_hop determines how we bin the data for the threshold definition:
    - Threshold 2: 1-hop vs 2+ hops
    - Threshold 3: 1-2 hop vs 3+ hops
    - Threshold 4: 1-3 hop vs 4+ hops

    However, for the overlay plot, we want to show the raw accuracy per hop count
    but highlight the threshold point.
    """
    hop_data = defaultdict(lambda: {'correct': 0, 'total': 0})

    for record in data:
        hop = record['chain_length']
        if record['correctness']:
            hop_data[hop]['correct'] += 1
        hop_data[hop]['total'] += 1

    accuracy_by_hop = {}
    for hop in sorted(hop_data.keys()):
        correct = hop_data[hop]['correct']
        total = hop_data[hop]['total']
        if total > 0:
            accuracy_by_hop[hop] = (correct / total, total)
        else:
            accuracy_by_hop[hop] = (0.0, 0)

    return accuracy_by_hop


def plot_sensitivity_overlay(
    sensitivity_results: List[Dict],
    annotated_data: List[Dict],
    output_path: Path
) -> None:
    """
    Generate overlay plot of accuracy curves for different thresholds.

    The plot shows:
    1. Raw accuracy points for each hop count
    2. Lines connecting mean accuracies for each hop
    3. Vertical dashed lines at each threshold point (2, 3, 4 hops)
    4. Different colors for each threshold definition

    Args:
        sensitivity_results: List of threshold analysis results
        annotated_data: Raw annotated dataset
        output_path: Path to save the plot
    """
    # Calculate accuracy by hop for each threshold
    threshold_hops = [2, 3, 4]
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c']  # matplotlib default colors
    labels = [f'Threshold = {t} hops (p={r["p_value"]:.4f})'
             for t, r in zip(threshold_hops, sensitivity_results)]

    plt.figure(figsize=(12, 8))

    # Get all hop counts from data
    all_hops = sorted(set(r['chain_length'] for r in annotated_data))

    for idx, (threshold_hop, color, label) in enumerate(zip(threshold_hops, colors, labels)):
        accuracy_by_hop = calculate_accuracy_by_hop(annotated_data, threshold_hop)

        # Extract accuracy and hop values
        hops = []
        accuracies = []
        for hop in all_hops:
            if hop in accuracy_by_hop:
                acc, count = accuracy_by_hop[hop]
                if count > 0:  # Only plot if we have data
                    hops.append(hop)
                    accuracies.append(acc)

        if hops:
            # Plot scatter points
            plt.scatter(hops, accuracies, color=color, alpha=0.6, s=50, label=label)
            # Plot connecting line
            plt.plot(hops, accuracies, color=color, alpha=0.8, linewidth=2)

    # Add vertical dashed lines at threshold points
    for threshold_hop in threshold_hops:
        plt.axvline(x=threshold_hop, color='gray', linestyle='--',
                   alpha=0.7, linewidth=1.5)

    # Configure plot
    plt.xlabel('Chain Length (Hops)', fontsize=12)
    plt.ylabel('Accuracy Rate', fontsize=12)
    plt.title('Sensitivity Analysis: Accuracy vs. Chain Length\n'
             'Overlay of Different Threshold Definitions', fontsize=14)
    plt.legend(loc='best', fontsize=10)
    plt.grid(True, alpha=0.3)
    plt.xticks(all_hops)
    plt.ylim(0, 1.05)

    # Add annotation about significance
    significant_count = sum(1 for r in sensitivity_results if r['is_significant'])
    total_count = len(sensitivity_results)
    annotation_text = f'Significant thresholds: {significant_count}/{total_count}'
    plt.annotate(annotation_text,
                xy=(0.02, 0.98),
                xycoords='axes fraction',
                fontsize=10,
                verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    # Save plot
    ensure_dir(output_path.parent)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    logger.info(f"Plot saved to: {output_path}")


def main() -> None:
    """Main entry point for sensitivity overlay plot generation."""
    logger.info("Starting sensitivity overlay plot generation")

    try:
        # Load data
        logger.info("Loading sensitivity results...")
        sensitivity_results = load_sensitivity_results()
        logger.info(f"Loaded {len(sensitivity_results)} threshold results")

        logger.info("Loading annotated data...")
        annotated_data = load_annotated_data()
        logger.info(f"Loaded {len(annotated_data)} records")

        # Generate plot
        output_path = get_path("data/processed/sensitivity_overlay.png")
        plot_sensitivity_overlay(sensitivity_results, annotated_data, output_path)

        logger.info("Sensitivity overlay plot generation completed successfully")

    except FileNotFoundError as e:
        logger.error(f"Missing required data file: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error generating plot: {e}")
        raise


if __name__ == "__main__":
    main()