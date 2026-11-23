"""
Plotting utilities for llmXive LatentSkill Extension.
Generates static plots for the final report.
"""
import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging

# Try to import matplotlib, fail gracefully if not present
try:
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    import matplotlib.pyplot as plt
    import numpy as np
except ImportError:
    logger = logging.getLogger(__name__)
    logger.error("matplotlib is required for plotting. Install via: pip install matplotlib")
    sys.exit(1)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def plot_success_rate_vs_k(sensitivity_data: Optional[Dict[str, Any]], output_path: Path) -> None:
    """Plot Success Rate vs Top-k values."""
    if not sensitivity_data or 'results' not in sensitivity_data:
        logger.warning("No sensitivity data available for plotting success rate vs k.")
        return

    k_values = []
    success_rates = []
    
    # Extract data from sensitivity.yaml structure
    results = sensitivity_data.get('results', [])
    for item in results:
        if isinstance(item, dict) and 'k' in item and 'mean_success' in item:
            k_values.append(item['k'])
            success_rates.append(item['mean_success'])
    
    if not k_values:
        logger.warning("No valid k/success data found in sensitivity results.")
        return

    plt.figure(figsize=(10, 6))
    plt.plot(k_values, success_rates, marker='o', linestyle='-', color='b')
    plt.xlabel('Top-k Value')
    plt.ylabel('Mean Success Rate')
    plt.title('Success Rate vs Top-k')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    logger.info(f"Saved success rate plot to {output_path}")

def plot_text_weight_correlation(linearity_data: Optional[Dict[str, Any]], output_path: Path) -> None:
    """Plot Text-Weight Correlation (if scatter data is available)."""
    # Note: Current linearity_validation.json only contains correlation coefficient.
    # If we had raw pairs, we would plot them. For now, we create a summary plot.
    if not linearity_data:
        logger.warning("No linearity data available for plotting.")
        return

    corr_coeff = linearity_data.get('correlation_coefficient')
    if corr_coeff is None:
        logger.warning("Correlation coefficient not found in linearity data.")
        return

    plt.figure(figsize=(8, 6))
    plt.bar(['Pearson r'], [corr_coeff], color=['green' if corr_coeff > 0.5 else 'orange'])
    plt.ylabel('Correlation Coefficient')
    plt.title('Text-Weight Space Correlation')
    plt.ylim(-1, 1)
    plt.axhline(y=0, color='k', linestyle='--', alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    logger.info(f"Saved correlation plot to {output_path}")

def plot_latency_breakdown(latency_data: Optional[Dict[str, Any]], output_path: Path) -> None:
    """Plot Latency Breakdown."""
    if not latency_data:
        logger.warning("No latency data available for plotting.")
        return

    labels = []
    values = []
    
    metrics = [
        ('embedding_latency_ms', 'Embedding'),
        ('retrieval_latency_ms', 'Retrieval'),
        ('interpolation_latency_ms', 'Interpolation')
    ]

    for key, label in metrics:
        val = latency_data.get(key)
        if val is not None:
            labels.append(label)
            values.append(val)

    if not values:
        logger.warning("No valid latency metrics found.")
        return

    plt.figure(figsize=(10, 6))
    plt.bar(labels, values, color=['skyblue', 'lightgreen', 'salmon'])
    plt.ylabel('Latency (ms)')
    plt.title('Skill Selection Latency Breakdown')
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    logger.info(f"Saved latency breakdown plot to {output_path}")

def main():
    parser = argparse.ArgumentParser(description='Generate static plots for the final report.')
    parser.add_argument('--input', type=str, required=True, help='Path to results directory (e.g., data/results)')
    parser.add_argument('--output', type=str, required=True, help='Path to output plots directory (e.g., reports/plots)')
    args = parser.parse_args()

    results_dir = Path(args.input)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load data
    sensitivity = None
    linearity = None
    latency = None

    if (results_dir / 'sensitivity.yaml').exists():
        import yaml
        with open(results_dir / 'sensitivity.yaml', 'r') as f:
            sensitivity = yaml.safe_load(f)
    
    if (results_dir / 'linearity_validation.json').exists():
        with open(results_dir / 'linearity_validation.json', 'r') as f:
            linearity = json.load(f)

    if (results_dir / 'latency_metrics.json').exists():
        with open(results_dir / 'latency_metrics.json', 'r') as f:
            latency = json.load(f)

    # Generate plots
    plot_success_rate_vs_k(sensitivity, output_dir / 'success_rate_vs_k.png')
    plot_text_weight_correlation(linearity, output_dir / 'text_weight_correlation.png')
    plot_latency_breakdown(latency, output_dir / 'latency_breakdown.png')

    logger.info("All plots generated successfully.")

if __name__ == '__main__':
    main()