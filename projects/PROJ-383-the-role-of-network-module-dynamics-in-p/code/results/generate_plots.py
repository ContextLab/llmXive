"""
Generate visualizations for the statistical analysis results.

This module creates:
1. Histogram of the null distribution from the permutation test.
2. Sensitivity analysis plot showing p-values across different window lengths.

Outputs are saved to:
- data/results/plots/null_dist.png
- data/results/plots/sensitivity_plot.png
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib

# Ensure non-interactive backend for server environments
matplotlib.use('Agg')

from utils.logging_config import setup_logging

# Configure logging
logger = logging.getLogger(__name__)
setup_logging()

# Constants
RESULTS_DIR = Path("data/results")
PLOTS_DIR = RESULTS_DIR / "plots"
STATISTICS_FILE = RESULTS_DIR / "statistical_report.json"
SENSITIVITY_FILE = RESULTS_DIR / "sensitivity_analysis.json"

def load_statistics_results() -> Optional[Dict[str, Any]]:
    """Load the statistical report containing permutation test results."""
    if not STATISTICS_FILE.exists():
        logger.error(f"Statistical report not found at {STATISTICS_FILE}")
        return None
    
    try:
        with open(STATISTICS_FILE, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse statistical report: {e}")
        return None

def load_sensitivity_results() -> Optional[Dict[str, Any]]:
    """Load the sensitivity analysis results."""
    if not SENSITIVITY_FILE.exists():
        logger.error(f"Sensitivity analysis results not found at {SENSITIVITY_FILE}")
        return None
    
    try:
        with open(SENSITIVITY_FILE, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse sensitivity analysis results: {e}")
        return None

def ensure_plots_directory():
    """Create the plots directory if it doesn't exist."""
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured plots directory exists: {PLOTS_DIR}")

def plot_null_distribution(null_distribution: List[float], observed_stat: float, output_path: Path):
    """
    Generate a histogram of the null distribution with the observed statistic marked.

    Args:
        null_distribution: List of correlation coefficients from permutation test.
        observed_stat: The observed partial Spearman correlation coefficient.
        output_path: Path to save the plot.
    """
    if not null_distribution:
        logger.warning("Null distribution is empty, skipping plot generation.")
        return

    plt.figure(figsize=(10, 6))
    
    # Plot histogram of null distribution
    n, bins, patches = plt.hist(
        null_distribution, 
        bins=50, 
        color='skyblue', 
        edgecolor='black', 
        alpha=0.7, 
        label='Null Distribution'
    )
    
    # Add vertical line for observed statistic
    plt.axvline(
        observed_stat, 
        color='red', 
        linestyle='dashed', 
        linewidth=2, 
        label=f'Observed r = {observed_stat:.4f}'
    )
    
    # Calculate p-value for annotation (two-tailed)
    extreme_count = sum(1 for x in null_distribution if abs(x) >= abs(observed_stat))
    p_value = extreme_count / len(null_distribution)
    
    plt.title(
        f'Null Distribution of Partial Spearman Correlation\n'
        f'(p-value = {p_value:.4f})',
        fontsize=14
    )
    plt.xlabel('Correlation Coefficient (r)', fontsize=12)
    plt.ylabel('Frequency', fontsize=12)
    plt.legend(fontsize=10)
    plt.grid(axis='y', alpha=0.3)
    
    # Save plot
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Saved null distribution plot to {output_path}")

def plot_sensitivity_analysis(sensitivity_results: Dict[str, Any], output_path: Path):
    """
    Generate a plot of p-values across different window lengths.

    Args:
        sensitivity_results: Dictionary containing window lengths and corresponding p-values.
        output_path: Path to save the plot.
    """
    window_lengths = sensitivity_results.get('window_lengths', [])
    p_values = sensitivity_results.get('p_values', [])
    
    if not window_lengths or not p_values:
        logger.warning("Sensitivity analysis data is empty, skipping plot generation.")
        return

    plt.figure(figsize=(10, 6))
    
    # Plot p-values
    plt.plot(
        window_lengths, 
        p_values, 
        marker='o', 
        linestyle='-', 
        color='green', 
        linewidth=2, 
        markersize=8, 
        label='P-value'
    )
    
    # Add horizontal line at significance threshold (0.05)
    plt.axhline(
        y=0.05, 
        color='red', 
        linestyle='--', 
        linewidth=1.5, 
        label='Significance Threshold (α = 0.05)'
    )
    
    # Fill area above/below threshold for visual clarity
    plt.fill_between(
        window_lengths, 
        p_values, 
        0.05, 
        where=(np.array(p_values) < 0.05), 
        interpolate=True, 
        color='green', 
        alpha=0.2, 
        label='Significant (p < 0.05)'
    )
    plt.fill_between(
        window_lengths, 
        p_values, 
        0.05, 
        where=(np.array(p_values) >= 0.05), 
        interpolate=True, 
        color='red', 
        alpha=0.1, 
        label='Not Significant (p ≥ 0.05)'
    )
    
    plt.title(
        'Sensitivity Analysis: P-values Across Window Lengths',
        fontsize=14
    )
    plt.xlabel('Window Length (seconds)', fontsize=12)
    plt.ylabel('P-value', fontsize=12)
    plt.legend(fontsize=10)
    plt.grid(True, alpha=0.3)
    plt.ylim(bottom=0)
    
    # Save plot
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Saved sensitivity analysis plot to {output_path}")

def main():
    """Main function to generate all required plots."""
    logger.info("Starting plot generation for statistical analysis results.")
    
    # Ensure output directory exists
    ensure_plots_directory()
    
    # Load statistical results for null distribution plot
    stats_results = load_statistics_results()
    if stats_results:
        null_dist = stats_results.get('null_distribution', [])
        observed_r = stats_results.get('observed_correlation', 0.0)
        
        if null_dist:
            null_dist_path = PLOTS_DIR / "null_dist.png"
            plot_null_distribution(null_dist, observed_r, null_dist_path)
        else:
            logger.warning("No null distribution found in statistical results.")
    else:
        logger.warning("Could not load statistical results for null distribution plot.")
    
    # Load sensitivity analysis results
    sens_results = load_sensitivity_results()
    if sens_results:
        sensitivity_path = PLOTS_DIR / "sensitivity_plot.png"
        plot_sensitivity_analysis(sens_results, sensitivity_path)
    else:
        logger.warning("Could not load sensitivity analysis results.")
    
    logger.info("Plot generation completed.")

if __name__ == "__main__":
    main()