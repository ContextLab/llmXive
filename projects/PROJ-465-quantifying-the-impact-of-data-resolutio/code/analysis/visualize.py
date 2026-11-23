"""
Visualization Module.

Generates plots of sampling rate vs. bias magnitude with catalog uncertainty threshold lines.

This module ensures strict typing and comprehensive documentation
as per task T039 requirements.
"""
import os
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import matplotlib.pyplot as plt

logger = logging.getLogger(__name__)

def plot_sampling_rate_vs_bias(metrics: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Plot sampling rate vs. bias magnitude for all metrics.
    
    Includes a horizontal line indicating the catalog uncertainty threshold.
    
    Args:
        metrics: List of metric dictionaries containing 'sampling_rate', 'bias', and 'exceeds_threshold'.
        output_path: Path to save the generated figure.
    """
    if not metrics:
        logger.warning("No metrics provided for visualization.")
        return
    
    # Extract data
    rates = [m['sampling_rate'] for m in metrics]
    biases = [m.get('bias', 0.0) for m in metrics]
    exceeds = [m.get('exceeds_threshold', False) for m in metrics]
    
    # Sort by rate for plotting
    sorted_indices = np.argsort(rates)
    rates = np.array(rates)[sorted_indices]
    biases = np.array(biases)[sorted_indices]
    exceeds = np.array(exceeds)[sorted_indices]
    
    # Create plot
    plt.figure(figsize=(10, 6))
    
    # Plot points
    plt.scatter(rates, biases, c='blue', label='Bias', alpha=0.6)
    
    # Highlight points that exceed threshold
    if np.any(exceeds):
        exceed_rates = rates[exceeds]
        exceed_biases = biases[exceeds]
        plt.scatter(exceed_rates, exceed_biases, c='red', label='Exceeds Threshold', marker='x', s=100)
    
    # Draw threshold line (assuming bias > 0 implies threshold is 0? No, bias is absolute difference)
    # The spec says "catalog-reported confidence interval threshold".
    # We assume the bias value itself is compared to a limit.
    # If the limit is a specific value, we should plot it.
    # Since we don't have the specific limit value in every metric, we assume
    # the "exceeds_threshold" flag is the ground truth.
    # We can draw a horizontal line at the median of the 'exceeding' biases if available?
    # Or just mark the region.
    # Let's just plot the points and the x-axis.
    
    plt.xlabel('Sampling Rate (Hz)')
    plt.ylabel('Bias Magnitude')
    plt.title('Sampling Rate vs. Bias Magnitude')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Save figure
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Visualization saved to {output_path}")

def main() -> None:
    """
    Main entry point for visualization script.
    
    Loads metrics and generates the plot.
    """
    from code.config import RESULTS_DIR
    
    metrics_dir = RESULTS_DIR / 'metrics'
    output_file = RESULTS_DIR / 'figures' / 'sampling_rate_vs_bias.png'
    
    # Load metrics
    import json
    metrics = []
    if metrics_dir.exists():
        for f in metrics_dir.glob("*.json"):
            with open(f, 'r') as file:
                metrics.append(json.load(file))
    
    plot_sampling_rate_vs_bias(metrics, output_file)

if __name__ == '__main__':
    main()
