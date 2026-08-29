"""
T024c: Generate convergence plot artifact.
Creates data/analysis/convergence_plot.png showing decay rate variance across seeds.
"""
import os
import sys
import json
import logging
import argparse
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_convergence_results(filepath: str) -> dict:
    """Load convergence results from JSON file."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Convergence results file not found: {filepath}")
    
    with open(filepath, 'r') as f:
        return json.load(f)

def plot_convergence_results(results: dict, output_path: str) -> None:
    """
    Generate a plot showing decay rate variance across seeds for each graph class.
    
    Args:
        results: Dictionary containing convergence test results with decay rates per seed
        output_path: Path to save the plot
    """
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    # Extract data for plotting
    graph_classes = []
    mean_decay_rates = []
    std_decay_rates = []
    seed_counts = []
    graph_ids = []

    for graph_id, data in results.items():
        class_name = data.get('class', 'Unknown')
        decay_rates = data.get('decay_rates', [])
        
        if not decay_rates:
            logger.warning(f"No decay rates found for graph {graph_id}, skipping.")
            continue

        mean_rate = np.mean(decay_rates)
        std_rate = np.std(decay_rates)
        
        graph_classes.append(class_name)
        mean_decay_rates.append(mean_rate)
        std_decay_rates.append(std_rate)
        seed_counts.append(len(decay_rates))
        graph_ids.append(graph_id)

    if not graph_classes:
        raise ValueError("No valid convergence data found to plot.")

    # Create the plot
    fig, ax = plt.subplots(figsize=(12, 8))
    
    x_positions = range(len(graph_classes))
    width = 0.6

    # Plot mean decay rates with error bars
    bars = ax.bar(
        x_positions, 
        mean_decay_rates, 
        yerr=std_decay_rates, 
        capsize=5, 
        width=width, 
        color='steelblue', 
        edgecolor='black',
        alpha=0.8
    )

    # Customize plot
    ax.set_xlabel('Graph Class', fontsize=12, fontweight='bold')
    ax.set_ylabel('Decay Rate (λ)', fontsize=12, fontweight='bold')
    ax.set_title('Convergence Analysis: Decay Rate Variance Across Seeds', fontsize=14, fontweight='bold')
    ax.set_xticks(x_positions)
    ax.set_xticklabels([f'{cls}\n(N={n})' for cls, n in zip(graph_classes, seed_counts)], rotation=45, ha='right')
    
    # Add grid for readability
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    ax.set_axisbelow(True)

    # Add annotations for standard deviation values
    for i, (bar, std_val) in enumerate(zip(bars, std_decay_rates)):
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2.,
            height + std_val,
            f'±{std_val:.4f}',
            ha='center',
            va='bottom',
            fontsize=10,
            fontweight='bold'
        )

    # Add a text box with summary statistics
    summary_text = "Convergence Criteria: std/mean < 0.01\n"
    passed_count = 0
    for i in range(len(mean_decay_rates)):
        if mean_decay_rates[i] != 0:
            ratio = std_decay_rates[i] / abs(mean_decay_rates[i])
            if ratio < 0.01:
                passed_count += 1
    
    summary_text += f"Graphs Passing Convergence: {passed_count}/{len(graph_classes)}"
    
    props = dict(boxstyle='round', facecolor='wheat', alpha=0.8)
    ax.text(
        0.02, 0.98, summary_text,
        transform=ax.transAxes,
        fontsize=10,
        verticalalignment='top',
        bbox=props
    )

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    logger.info(f"Convergence plot saved to: {output_path}")

def main():
    """Main entry point for the convergence plot generation."""
    parser = argparse.ArgumentParser(
        description='Generate convergence plot from simulation results.'
    )
    parser.add_argument(
        '--input', '-i',
        type=str,
        default='data/analysis/convergence_results.json',
        help='Path to convergence results JSON file'
    )
    parser.add_argument(
        '--output', '-o',
        type=str,
        default='data/analysis/convergence_plot.png',
        help='Path to save the output plot'
    )
    
    args = parser.parse_args()
    
    logger.info(f"Loading convergence results from: {args.input}")
    try:
        results = load_convergence_results(args.input)
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in results file: {e}")
        sys.exit(1)

    logger.info(f"Generating convergence plot...")
    try:
        plot_convergence_results(results, args.output)
        logger.info("Successfully generated convergence plot.")
    except ValueError as e:
        logger.error(str(e))
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to generate plot: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()