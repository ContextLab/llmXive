"""
Visualization utilities for RSA matrices and decoding accuracy.
"""
import matplotlib.pyplot as plt
import numpy as np
import logging
from pathlib import Path
import json
import code.config as config

logger = logging.getLogger(__name__)

def plot_rsa_matrix(matrix, title="RSA Matrix", save_path=None):
    """
    Plot a Representational Similarity Analysis (RSA) dissimilarity matrix.
    """
    plt.figure(figsize=(8, 6))
    plt.imshow(matrix, cmap='coolwarm', interpolation='nearest')
    plt.colorbar(label='Dissimilarity')
    plt.title(title)
    plt.xlabel("Events")
    plt.ylabel("Events")

    if save_path:
        plt.savefig(save_path, dpi=300)
        logger.info(f"RSA matrix saved to {save_path}")
    else:
        # Default save path if not provided
        default_path = Path(config.FIGURES_DIR) / f"rsa_{title.replace(' ', '_')}.png"
        plt.savefig(default_path, dpi=300)
        logger.info(f"RSA matrix saved to {default_path}")
    plt.close()

def plot_decoding_accuracy(accuracies, chance_level, title="Decoding Accuracy", save_path=None):
    """
    Plot decoding accuracy with chance baseline.
    """
    plt.figure(figsize=(8, 6))
    plt.bar(range(len(accuracies)), accuracies, color='skyblue', label='Accuracy')
    plt.axhline(y=chance_level, color='r', linestyle='--', label=f'Chance ({chance_level:.2f})')
    plt.xlabel("Fold / Category")
    plt.ylabel("Accuracy")
    plt.title(title)
    plt.legend()

    if save_path:
        plt.savefig(save_path, dpi=300)
        logger.info(f"Decoding accuracy plot saved to {save_path}")
    else:
        default_path = Path(config.FIGURES_DIR) / f"decoding_{title.replace(' ', '_')}.png"
        plt.savefig(default_path, dpi=300)
        logger.info(f"Decoding accuracy plot saved to {default_path}")
    plt.close()

def plot_early_late_roi_comparison(stats_path, output_path=None):
    """
    Visualize top differing ROIs (mPFC, hippocampus) based on Early vs. Late event RSA metrics.
    
    Reads group statistics from a JSON file (produced by T023) and generates a 
    bar chart comparing Early-Late dissimilarity against Early-Early dissimilarity 
    for key ROIs.
    
    Args:
        stats_path (str): Path to the JSON file containing group RSA stats 
                          (schema: {roi: {early_late: float, early_early: float}}).
        output_path (str, optional): Path to save the figure. Defaults to 
                                   results/rsa_heatmaps.png if not provided.
    """
    # Load statistics
    with open(stats_path, 'r') as f:
        stats = json.load(f)
    
    # Filter for top ROIs of interest if they exist, otherwise use all available
    target_rois = ['mPFC', 'hippocampus', 'PCC', 'lateral_temporal']
    available_rois = [r for r in target_rois if r in stats]
    
    if not available_rois:
        logger.warning(f"No target ROIs found in {stats_path}. Using all available keys.")
        available_rois = list(stats.keys())
    
    early_late_vals = []
    early_early_vals = []
    labels = []
    
    for roi in available_rois:
        data = stats[roi]
        if 'early_late' in data and 'early_early' in data:
            early_late_vals.append(data['early_late'])
            early_early_vals.append(data['early_early'])
            labels.append(roi)
        else:
            logger.warning(f"Skipping ROI {roi}: missing expected keys.")
    
    if not labels:
        raise ValueError("No valid data found to plot for Early vs. Late comparison.")
    
    x = np.arange(len(labels))
    width = 0.35
    
    fig, ax = plt.subplots(figsize=(10, 6))
    rects1 = ax.bar(x - width/2, early_late_vals, width, label='Early vs. Late', color='#1f77b4')
    rects2 = ax.bar(x + width/2, early_early_vals, width, label='Early vs. Early', color='#ff7f0e')
    
    ax.set_ylabel('Dissimilarity (1 - Pearson r)')
    ax.set_title('Early vs. Late Event Pattern Comparison by ROI')
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.legend()
    
    # Add value labels on bars
    def autolabel(rects):
        for rect in rects:
            height = rect.get_height()
            ax.annotate(f'{height:.3f}',
                        xy=(rect.get_x() + rect.get_width() / 2, height),
                        xytext=(0, 3),
                        textcoords="offset points",
                        ha='center', va='bottom', fontsize=9)
    
    autolabel(rects1)
    autolabel(rects2)
    
    plt.tight_layout()
    
    if output_path is None:
        output_path = Path(config.RESULTS_DIR) / "rsa_heatmaps.png"
    else:
        output_path = Path(output_path)
        
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    plt.savefig(output_path, dpi=300)
    logger.info(f"ROI comparison plot saved to {output_path}")
    plt.close()

def plot_stability_metrics(stability_data, output_path=None):
    """
    Plot stability metrics if available.
    """
    if output_path is None:
        output_path = Path(config.RESULTS_DIR) / "stability_metrics.png"
        
    # Implementation depends on exact schema of stability_data
    # Placeholder for future integration if T025 provides specific structure
    pass

def main():
    """
    Entry point to generate the required visualization for T024.
    Expects results/group_rsa_stats.json to exist (produced by T023).
    """
    stats_file = Path(config.RESULTS_DIR) / "group_rsa_stats.json"
    if not stats_file.exists():
        raise FileNotFoundError(f"Required input file not found: {stats_file}. "
                                "Ensure T023 has completed successfully.")
    
    output_file = Path(config.RESULTS_DIR) / "rsa_heatmaps.png"
    plot_early_late_roi_comparison(str(stats_file), str(output_file))
    print(f"Visualization complete: {output_file}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()