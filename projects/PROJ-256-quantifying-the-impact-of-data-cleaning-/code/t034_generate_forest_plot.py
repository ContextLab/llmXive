"""
Task T034: Generate forest plot of p-value shifts.

Reads baseline and cleaned metrics from data/processed/, calculates p-value shifts,
and generates a forest plot saved to output/forest_plot_pvalue_shifts.png.
"""
import os
import json
import logging
from typing import List, Dict, Any, Optional
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import pandas as pd
import numpy as np

from utils import setup_logging, pin_random_seed
from config import get_config

# Configure logging
logger = logging.getLogger(__name__)

def load_json(filepath: str) -> Dict[str, Any]:
    """Load JSON file."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
    with open(filepath, 'r') as f:
        return json.load(f)

def calculate_p_value_shift(baseline_p: float, cleaned_p: float) -> float:
    """Calculate absolute p-value shift: |cleaned - baseline|."""
    return abs(cleaned_p - baseline_p)

def load_metrics_for_plotting() -> List[Dict[str, Any]]:
    """
    Load baseline and cleaned metrics and combine them for plotting.
    Returns a list of dictionaries containing dataset info and p-value shifts.
    """
    config = get_config()
    baseline_path = os.path.join(config['OUTPUT_PATH'], 'baseline_metrics.json')
    cleaned_path = os.path.join(config['OUTPUT_PATH'], 'cleaned_metrics.json')

    try:
        baseline_data = load_json(baseline_path)
        cleaned_data = load_json(cleaned_path)
    except FileNotFoundError as e:
        logger.error(f"Missing required metrics file: {e}")
        raise

    # Normalize structure if needed (handle both list and dict formats)
    if isinstance(baseline_data, dict):
        baseline_list = list(baseline_data.values())
    else:
        baseline_list = baseline_data

    if isinstance(cleaned_data, dict):
        cleaned_list = list(cleaned_data.values())
    else:
        cleaned_list = cleaned_data

    # Create a mapping for quick lookup
    cleaned_map = {}
    for item in cleaned_list:
        # Handle different possible key names for dataset identifier
        ds_id = item.get('dataset_id') or item.get('dataset_name') or item.get('name')
        if ds_id:
            cleaned_map[ds_id] = item

    plot_data = []
    for baseline_item in baseline_list:
        ds_id = baseline_item.get('dataset_id') or baseline_item.get('dataset_name') or baseline_item.get('name')
        if not ds_id:
            logger.warning(f"Skipping baseline item without identifier: {baseline_item}")
            continue

        cleaned_item = cleaned_map.get(ds_id)
        if not cleaned_item:
            logger.warning(f"No cleaned metrics found for dataset: {ds_id}")
            continue

        # Extract p-values (handle different possible structures)
        # Try to find p-value in various possible locations
        baseline_p = None
        cleaned_p = None

        # Check top level
        if 'p_value' in baseline_item:
            baseline_p = baseline_item['p_value']
        elif 'results' in baseline_item and isinstance(baseline_item['results'], dict) and 'p_value' in baseline_item['results']:
            baseline_p = baseline_item['results']['p_value']
        elif 't_test' in baseline_item and isinstance(baseline_item['t_test'], dict) and 'p_value' in baseline_item['t_test']:
            baseline_p = baseline_item['t_test']['p_value']

        if 'p_value' in cleaned_item:
            cleaned_p = cleaned_item['p_value']
        elif 'results' in cleaned_item and isinstance(cleaned_item['results'], dict) and 'p_value' in cleaned_item['results']:
            cleaned_p = cleaned_item['results']['p_value']
        elif 't_test' in cleaned_item and isinstance(cleaned_item['t_test'], dict) and 'p_value' in cleaned_item['t_test']:
            cleaned_p = cleaned_item['t_test']['p_value']

        if baseline_p is None or cleaned_p is None:
            logger.warning(f"Could not extract p-values for dataset: {ds_id}")
            continue

        shift = calculate_p_value_shift(baseline_p, cleaned_p)
        
        # Determine cleaning strategy from the cleaned item
        strategy = cleaned_item.get('strategy', cleaned_item.get('cleaning_strategy', 'Unknown'))
        
        plot_data.append({
            'dataset_id': ds_id,
            'strategy': strategy,
            'baseline_p': baseline_p,
            'cleaned_p': cleaned_p,
            'shift': shift,
            'baseline_significant': baseline_p < 0.05,
            'cleaned_significant': cleaned_p < 0.05
        })

    return plot_data

def generate_forest_plot(plot_data: List[Dict[str, Any]], output_path: str):
    """
    Generate a forest plot showing p-value shifts for each dataset/strategy combination.
    
    The plot shows:
    - Dataset names on the y-axis
    - P-value shifts on the x-axis (absolute difference)
    - Bars indicating the magnitude of the shift
    - Color coding for direction of change
    """
    if not plot_data:
        logger.error("No data available for forest plot generation.")
        return False

    # Sort by shift magnitude for better visualization
    plot_data_sorted = sorted(plot_data, key=lambda x: x['shift'], reverse=True)

    n = len(plot_data_sorted)
    fig, ax = plt.subplots(figsize=(12, max(6, n * 0.6)))

    # Create y-ticks
    y_pos = np.arange(n)
    labels = [f"{item['dataset_id']}\n({item['strategy']})" for item in plot_data_sorted]
    shifts = [item['shift'] for item in plot_data_sorted]

    # Color based on whether significance changed
    colors = []
    for item in plot_data_sorted:
        if item['baseline_significant'] != item['cleaned_significant']:
            colors.append('red')  # Significance changed
        else:
            colors.append('steelblue')  # Significance unchanged

    # Create horizontal bars
    bars = ax.barh(y_pos, shifts, color=colors, alpha=0.8, edgecolor='black')

    # Add value labels on bars
    for i, (bar, shift) in enumerate(zip(bars, shifts)):
        width = bar.get_width()
        label_x = width + 0.001 if width > 0 else width - 0.001
        ax.text(label_x, bar.get_y() + bar.get_height()/2, 
               f'{shift:.3f}', va='center', fontsize=9)

    # Set labels and title
    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=10)
    ax.set_xlabel('Absolute P-value Shift |p_cleaned - p_baseline|', fontsize=12)
    ax.set_title('Forest Plot: P-value Shifts by Dataset and Cleaning Strategy', fontsize=14, fontweight='bold')
    ax.set_xlim(left=0)

    # Add reference line for significance change threshold (optional visual aid)
    ax.axvline(x=0.05, color='gray', linestyle='--', alpha=0.5, label='0.05 shift reference')

    # Add legend
    legend_elements = [
        mpatches.Patch(color='steelblue', label='Significance Status Unchanged'),
        mpatches.Patch(color='red', label='Significance Status Changed')
    ]
    ax.legend(handles=legend_elements, loc='upper right')

    # Tight layout
    plt.tight_layout()

    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Save figure
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    logger.info(f"Forest plot saved to: {output_path}")
    return True

def main():
    """Main entry point for T034."""
    # Setup logging
    log_level = os.getenv('LOG_LEVEL', 'INFO')
    logger = setup_logging(log_level)
    
    # Pin random seed for reproducibility
    seed = int(os.getenv('RANDOM_SEED', 42))
    pin_random_seed(seed)

    logger.info("Starting T034: Generate forest plot of p-value shifts")

    try:
        # Load and process metrics
        plot_data = load_metrics_for_plotting()
        
        if not plot_data:
            logger.error("No valid data found for plotting. Check baseline_metrics.json and cleaned_metrics.json.")
            return 1

        logger.info(f"Loaded {len(plot_data)} dataset/strategy combinations for plotting")

        # Determine output path
        config = get_config()
        output_dir = config.get('OUTPUT_PATH', 'data/processed')
        # Ensure we output to 'output/' as per task requirement
        output_dir = 'output'
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        output_path = os.path.join(output_dir, 'forest_plot_pvalue_shifts.png')

        # Generate plot
        success = generate_forest_plot(plot_data, output_path)
        
        if success:
            logger.info("T034 completed successfully")
            return 0
        else:
            logger.error("Failed to generate forest plot")
            return 1

    except Exception as e:
        logger.exception(f"Error during T034 execution: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
