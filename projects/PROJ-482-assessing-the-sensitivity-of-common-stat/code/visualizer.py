"""
Visualizer module for the llmXive statistical sensitivity pipeline.

This module contains functions to load aggregated simulation results and
generate publication-ready visualizations. It focuses on plotting error rates
against sample sizes, comparing different statistical tests, and displaying
confidence intervals to illustrate the sensitivity of tests to dataset size.
"""

import os
import logging
from typing import Optional, List, Dict, Any
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for server environments
import matplotlib.pyplot as plt
import seaborn as sns

# Configure module-level logger
logger = logging.getLogger(__name__)

# Style settings for publication-ready plots
plt.style.use('seaborn-v0_8-whitegrid')
COLORS = {
    't-test': '#1f77b4',
    'anova': '#ff7f0e',
    'chi-squared': '#2ca02c',
    'fisher': '#d62728'
}
LINEWIDTHS = 2.5
CI_ALPHA = 0.3  # Transparency for confidence interval bands


def load_aggregated_results(filepath: str) -> pd.DataFrame:
    """
    Load aggregated simulation results from a CSV file.

    This function reads the processed error rate data (aggregated from raw p-values)
    into a pandas DataFrame for visualization.

    Args:
        filepath (str): Path to the CSV file containing aggregated results.
                        Expected columns: 'sample_size', 'distribution_type',
                        'test_type', 'error_rate', 'ci_lower', 'ci_upper'.

    Returns:
        pd.DataFrame: DataFrame containing the loaded results.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is empty.
    """
    if not os.path.exists(filepath):
        logger.error(f"Aggregated results file not found: {filepath}")
        raise FileNotFoundError(f"File not found: {filepath}")

    df = pd.read_csv(filepath)

    if df.empty:
        logger.error(f"Aggregated results file is empty: {filepath}")
        raise ValueError(f"File is empty: {filepath}")

    logger.info(f"Loaded {len(df)} rows from {filepath} for visualization.")
    return df


def plot_error_rate_vs_sample_size(df: pd.DataFrame, output_path: str, test_type: Optional[str] = None) -> None:
    """
    Generate a plot of error rate vs. sample size for a specific test or all tests.

    This function creates a line plot with confidence interval bands to show how
    the Type I error rate (or power) changes as the sample size increases.
    It handles multiple distributions and test types, allowing for comparison.

    Args:
        df (pd.DataFrame): Aggregated results DataFrame.
        output_path (str): Path where the plot will be saved.
        test_type (str, optional): If provided, only plot data for this specific test type.
                                   If None, plots all test types with distinct colors.
    """
    plt.figure(figsize=(12, 8))

    # Filter data if a specific test type is requested
    if test_type:
        plot_df = df[df['test_type'] == test_type]
        if plot_df.empty:
            logger.warning(f"No data found for test type: {test_type}")
            return
        color = COLORS.get(test_type, 'gray')
        plot_data = [(test_type, plot_df, color)]
    else:
        # Group by test type to plot each with a unique color
        plot_data = []
        for t_type, group in df.groupby('test_type'):
            color = COLORS.get(t_type, 'gray')
            plot_data.append((t_type, group, color))

    # Plot each test type
    for t_name, group, color in plot_data:
        # Sort by sample size for smooth lines
        group_sorted = group.sort_values('sample_size')

        # Plot the main line
        plt.plot(group_sorted['sample_size'], group_sorted['error_rate'],
                 label=t_name, color=color, linewidth=LINEWIDTHS, marker='o', markersize=4)

        # Plot confidence interval bands
        if 'ci_lower' in group_sorted.columns and 'ci_upper' in group_sorted.columns:
            plt.fill_between(group_sorted['sample_size'],
                             group_sorted['ci_lower'],
                             group_sorted['ci_upper'],
                             color=color, alpha=CI_ALPHA)

    plt.xlabel('Sample Size (n)', fontsize=12)
    plt.ylabel('Error Rate (Type I or Power)', fontsize=12)
    plt.title('Statistical Test Sensitivity: Error Rate vs. Sample Size', fontsize=14, fontweight='bold')
    plt.legend(title='Test Type', fontsize=10)
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.tight_layout()

    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Error rate vs. sample size plot saved to {output_path}")


def plot_comparison_all_tests(df: pd.DataFrame, output_path: str) -> None:
    """
    Generate a comparison plot showing error rates for all tests across sample sizes.

    This function creates a faceted plot (or multi-line plot) that compares the
    performance of different statistical tests (t-test, ANOVA, Chi-squared)
    side-by-side to highlight differences in sensitivity to sample size.

    Args:
        df (pd.DataFrame): Aggregated results DataFrame.
        output_path (str): Path where the plot will be saved.
    """
    # Create a figure with subplots for each distribution type if present
    # Otherwise, just a single plot for all tests
    if 'distribution_type' in df.columns:
        distributions = df['distribution_type'].unique()
        n_plots = len(distributions)
        fig, axes = plt.subplots(1, n_plots, figsize=(5 * n_plots, 4), sharey=True)
        if n_plots == 1:
            axes = [axes]

        for idx, dist in enumerate(distributions):
            dist_df = df[df['distribution_type'] == dist]
            ax = axes[idx]

            for t_type, group in dist_df.groupby('test_type'):
                group_sorted = group.sort_values('sample_size')
                color = COLORS.get(t_type, 'gray')
                ax.plot(group_sorted['sample_size'], group_sorted['error_rate'],
                        label=t_type, color=color, linewidth=LINEWIDTHS, marker='o', markersize=4)
                if 'ci_lower' in group_sorted.columns and 'ci_upper' in group_sorted.columns:
                    ax.fill_between(group_sorted['sample_size'],
                                    group_sorted['ci_lower'],
                                    group_sorted['ci_upper'],
                                    color=color, alpha=CI_ALPHA)

            ax.set_title(f'Distribution: {dist}')
            ax.set_xlabel('Sample Size (n)')
            if idx == 0:
                ax.set_ylabel('Error Rate')
            ax.legend(fontsize=8)
            ax.grid(True, linestyle='--', alpha=0.6)

        plt.suptitle('Comparison of Statistical Tests by Distribution', fontsize=14, fontweight='bold')
        plt.tight_layout(rect=[0, 0, 1, 0.95])
    else:
        fig, ax = plt.subplots(figsize=(12, 6))
        for t_type, group in df.groupby('test_type'):
            group_sorted = group.sort_values('sample_size')
            color = COLORS.get(t_type, 'gray')
            ax.plot(group_sorted['sample_size'], group_sorted['error_rate'],
                    label=t_type, color=color, linewidth=LINEWIDTHS, marker='o', markersize=4)
            if 'ci_lower' in group_sorted.columns and 'ci_upper' in group_sorted.columns:
                ax.fill_between(group_sorted['sample_size'],
                                group_sorted['ci_lower'],
                                group_sorted['ci_upper'],
                                color=color, alpha=CI_ALPHA)

        ax.set_xlabel('Sample Size (n)')
        ax.set_ylabel('Error Rate')
        ax.set_title('Comparison of Statistical Tests', fontsize=14, fontweight='bold')
        ax.legend()
        ax.grid(True, linestyle='--', alpha=0.6)
        plt.tight_layout()

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Comparison plot saved to {output_path}")


def generate_all_plots(aggregated_df: pd.DataFrame, output_dir: str) -> None:
    """
    Generate all required visualization plots.

    This function acts as a factory to create the standard set of plots:
    1. Error rate vs. sample size for each test type individually.
    2. A comparison plot showing all tests together.

    Args:
        aggregated_df (pd.DataFrame): The aggregated results DataFrame.
        output_dir (str): Directory where the plots will be saved.
    """
    os.makedirs(output_dir, exist_ok=True)

    # Plot individual error rate curves
    for test_type in aggregated_df['test_type'].unique():
        plot_path = os.path.join(output_dir, f'error_rate_{test_type.replace(" ", "_")}.png')
        plot_error_rate_vs_sample_size(aggregated_df, plot_path, test_type=test_type)

    # Plot comparison
    comparison_path = os.path.join(output_dir, 'comparison_all_tests.png')
    plot_comparison_all_tests(aggregated_df, comparison_path)

    logger.info(f"All plots generated and saved to {output_dir}")


def main():
    """
    Entry point for the visualizer module when run as a script.

    This function demonstrates how to load data and generate plots.
    It expects a CSV file path as an argument or uses a default path.
    """
    import argparse

    parser = argparse.ArgumentParser(description='Generate visualization plots from simulation results.')
    parser.add_argument('--input', type=str, default='data/processed/error_rates.csv',
                        help='Path to the aggregated results CSV file.')
    parser.add_argument('--output', type=str, default='data/processed/plots',
                        help='Output directory for plots.')
    args = parser.parse_args()

    try:
        df = load_aggregated_results(args.input)
        generate_all_plots(df, args.output)
        logger.info("Visualization pipeline completed successfully.")
    except Exception as e:
        logger.error(f"Visualization pipeline failed: {e}")
        raise