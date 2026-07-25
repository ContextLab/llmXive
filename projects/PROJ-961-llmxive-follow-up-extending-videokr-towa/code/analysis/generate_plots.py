import csv
import json
import logging
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple, Any

import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for CI
import matplotlib.pyplot as plt
import numpy as np

from utils.config import get_project_root, get_path, ensure_dir

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_raw_annotated_data(filepath: str) -> List[Dict[str, Any]]:
    """
    Load the raw annotated dataset from CSV.
    Returns a list of dictionaries with 'chain_length' and 'correctness'.
    """
    data = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Ensure we have the required fields
                if 'chain_length' in row and 'correctness' in row:
                    try:
                        chain_len = int(row['chain_length'])
                        # correctness is usually 0 or 1 in these datasets
                        correct = float(row['correctness'])
                        data.append({
                            'chain_length': chain_len,
                            'correctness': correct
                        })
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Skipping row due to invalid data: {row}, error: {e}")
                        continue
    except FileNotFoundError:
        logger.error(f"File not found: {filepath}")
        raise
    return data

def load_binned_accuracy_data(filepath: str) -> Dict[str, float]:
    """
    Load binned accuracy data from a JSON file (produced by T019).
    Expected format: {"1": 0.85, "2": 0.72, "3+": 0.60}
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning(f"Binned accuracy file not found: {filepath}. Generating from raw data if needed.")
        return {}

def plot_continuous_accuracy(raw_data: List[Dict[str, Any]], output_path: str):
    """
    Generate a scatter plot of accuracy vs. exact chain_length.
    
    Requirements (FR-005, SC-003):
    1. Plot raw scatter points (individual records).
    2. Overlay a line connecting the MEAN accuracy of each discrete hop count.
    3. DO NOT use smoothing splines (LOESS, spline, etc.).
    """
    if not raw_data:
        logger.error("No data provided for continuous accuracy plot.")
        raise ValueError("Raw data list is empty.")

    # Extract data for plotting
    chain_lengths = [d['chain_length'] for d in raw_data]
    correct_values = [d['correctness'] for d in raw_data]

    # Calculate mean accuracy per discrete hop count for the line plot
    hop_means = defaultdict(list)
    for d in raw_data:
        hop_means[d['chain_length']].append(d['correctness'])
    
    sorted_hops = sorted(hop_means.keys())
    mean_accuracies = [np.mean(hop_means[h]) for h in sorted_hops]

    # Ensure output directory exists
    ensure_dir(str(Path(output_path).parent))

    plt.figure(figsize=(10, 6))
    
    # 1. Plot raw scatter points
    # Using a small alpha to handle overplotting and show density
    plt.scatter(
        chain_lengths, 
        correct_values, 
        color='gray', 
        alpha=0.3, 
        s=10, 
        label='Raw Records',
        edgecolors='none'
    )

    # 2. Plot line connecting means of discrete hops
    plt.plot(
        sorted_hops, 
        mean_accuracies, 
        color='red', 
        linewidth=2.5, 
        marker='o', 
        markersize=8,
        label='Mean Accuracy per Hop',
        zorder=5
    )

    plt.xlabel('Chain Length (Hops)', fontsize=12)
    plt.ylabel('Accuracy (Correctness)', fontsize=12)
    plt.title('Accuracy vs. Exact Chain Length (VideoKR)', fontsize=14)
    plt.xticks(sorted_hops)  # Ensure x-axis shows all integer hops present
    plt.ylim(0, 1.05)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend(loc='best')

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Continuous accuracy plot saved to: {output_path}")

def plot_binned_accuracy(binned_data: Dict[str, float], output_path: str):
    """
    Generate a bar plot of accuracy vs. hop bin (for T022b).
    """
    if not binned_data:
        logger.warning("No binned data provided for binned accuracy plot.")
        return

    bins = list(binned_data.keys())
    accuracies = list(binned_data.values())

    plt.figure(figsize=(10, 6))
    plt.bar(bins, accuracies, color='steelblue', alpha=0.8)
    
    plt.xlabel('Hop Bin', fontsize=12)
    plt.ylabel('Accuracy', fontsize=12)
    plt.title('Accuracy by Hop Bin', fontsize=14)
    plt.ylim(0, 1.05)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Add value labels on top of bars
    for i, v in enumerate(accuracies):
        plt.text(i, v + 0.02, f"{v:.2f}", ha='center', va='bottom', fontsize=10)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Binned accuracy plot saved to: {output_path}")

def main():
    project_root = get_project_root()
    
    # Define paths based on task dependencies
    raw_data_path = str(project_root / "data" / "processed" / "annotated_videokr.csv")
    binned_data_path = str(project_root / "data" / "processed" / "binned_accuracy.json")
    
    # Output paths
    continuous_plot_path = str(project_root / "data" / "processed" / "accuracy_vs_chain_length.png")
    binned_plot_path = str(project_root / "data" / "processed" / "accuracy_vs_bin.png")

    logger.info("Starting plot generation...")

    # 1. Generate Continuous Plot (T022a)
    try:
        logger.info(f"Loading raw data from {raw_data_path}")
        raw_data = load_raw_annotated_data(raw_data_path)
        logger.info(f"Loaded {len(raw_data)} records.")
        
        plot_continuous_accuracy(raw_data, continuous_plot_path)
    except FileNotFoundError:
        logger.error(f"Required raw data file not found: {raw_data_path}. "
                     "Please ensure T013 (annotate_graph.py) has completed successfully.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error generating continuous plot: {e}")
        raise

    # 2. Generate Binned Plot (T022b - optional but good to have if data exists)
    if Path(binned_data_path).exists():
        try:
            logger.info(f"Loading binned data from {binned_data_path}")
            binned_data = load_binned_accuracy_data(binned_data_path)
            plot_binned_accuracy(binned_data, binned_plot_path)
        except Exception as e:
            logger.warning(f"Could not generate binned plot: {e}")
    else:
        logger.info(f"Binned data file not found at {binned_data_path}. Skipping binned plot.")

    logger.info("Plot generation complete.")

if __name__ == "__main__":
    main()