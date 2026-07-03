"""
Visualization module for generating error rate plots.
"""
import os
import logging
from pathlib import Path
from typing import Optional

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np

# Configure logger for this module
logger = logging.getLogger(__name__)

def generate_error_rate_plot(
    results_path: str = "results/simulation_results.csv",
    output_path: str = "results/figures/error_rate_vs_alpha.png",
    nominal_alpha: float = 0.05
) -> None:
    """
    Generate a plot showing empirical error rate vs nominal alpha with 95% CI.

    This function reads the simulation results, calculates the aggregate metrics
    (Type I error rate and Power) per scaling method and distribution type,
    and plots the empirical error rate against the nominal alpha level (0.05),
    including 95% confidence intervals.

    Args:
        results_path: Path to the CSV file containing simulation results.
        output_path: Path where the plot will be saved.
        nominal_alpha: The nominal significance level (default 0.05).
    """
    logger.info(f"Loading simulation results from {results_path}")
    
    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load data
    if not os.path.exists(results_path):
        logger.error(f"Results file not found: {results_path}")
        raise FileNotFoundError(f"Results file not found: {results_path}")

    df = pd.read_csv(results_path)

    # Calculate aggregate metrics using the existing function
    # We expect calculate_aggregate_metrics to return a DataFrame with columns:
    # scaling_method, distribution_type, empirical_error_rate, ci_lower, ci_upper
    from analysis.metrics import calculate_aggregate_metrics

    try:
        metrics_df = calculate_aggregate_metrics(results_path, nominal_alpha=nominal_alpha)
    except Exception as e:
        logger.error(f"Failed to calculate aggregate metrics: {e}")
        raise

    logger.info(f"Calculated aggregate metrics for {len(metrics_df)} combinations")

    # Set up the plot style
    sns.set_theme(style="whitegrid", context="talk")
    fig, ax = plt.subplots(figsize=(12, 8))

    # Plot empirical error rates with confidence intervals
    # Group by scaling_method and distribution_type
    for (scaling_method, dist_type), group in metrics_df.groupby(['scaling_method', 'distribution_type']):
        # Calculate the average empirical error rate across distributions for each scaling method
        # or plot per distribution if needed. For clarity, we'll plot per scaling method aggregated.
        pass

    # Aggregate by scaling_method only for a cleaner comparison against nominal alpha
    # Calculate mean error rate and CI across all distributions for each scaling method
    summary_df = metrics_df.groupby('scaling_method').agg(
        mean_error_rate=('empirical_error_rate', 'mean'),
        std_error_rate=('empirical_error_rate', 'std'),
        count=('empirical_error_rate', 'count')
    ).reset_index()

    # Calculate 95% CI for the mean
    summary_df['ci_lower'] = summary_df['mean_error_rate'] - 1.96 * (summary_df['std_error_rate'] / np.sqrt(summary_df['count']))
    summary_df['ci_upper'] = summary_df['mean_error_rate'] + 1.96 * (summary_df['std_error_rate'] / np.sqrt(summary_df['count']))

    # Plot
    x_pos = np.arange(len(summary_df))
    ax.bar(x_pos, summary_df['mean_error_rate'], yerr=[
        summary_df['mean_error_rate'] - summary_df['ci_lower'],
        summary_df['ci_upper'] - summary_df['mean_error_rate']
    ], capsize=5, color=sns.color_palette("viridis", len(summary_df)), alpha=0.8, label='Empirical Error Rate')

    # Add nominal alpha line
    ax.axhline(y=nominal_alpha, color='red', linestyle='--', linewidth=2, label=f'Nominal Alpha ({nominal_alpha})')

    # Add labels and title
    ax.set_xticks(x_pos)
    ax.set_xticklabels(summary_df['scaling_method'])
    ax.set_ylabel('Empirical Type I Error Rate')
    ax.set_xlabel('Scaling Method')
    ax.set_title(f'Empirical Error Rate vs Nominal Alpha ({nominal_alpha}) with 95% CI')
    ax.legend(loc='upper right')
    ax.set_ylim(0, max(summary_df['ci_upper'].max(), nominal_alpha) * 1.2)

    # Add grid
    ax.grid(True, axis='y', linestyle='--', alpha=0.7)

    # Save the plot
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    logger.info(f"Error rate plot saved to {output_path}")
    plt.close()
