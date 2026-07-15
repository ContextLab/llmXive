"""
Visualizer module to generate publication-ready plots from aggregated results.
"""
import os
import logging
from typing import Optional, List, Dict, Any
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns

logger = logging.getLogger(__name__)

def load_aggregated_results(filepath: str) -> pd.DataFrame:
    """
    Load aggregated results from a CSV file.
    
    Args:
        filepath: Path to the CSV file.
        
    Returns:
        DataFrame with aggregated results.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Aggregated file not found: {filepath}")
    return pd.read_csv(filepath)

def plot_error_rate_vs_sample_size(df: pd.DataFrame, output_path: str) -> str:
    """
    Generate a plot of Error Rate vs. Sample Size with confidence intervals.
    
    Args:
        df: Aggregated DataFrame.
        output_path: Path to save the plot.
        
    Returns:
        Path to the saved plot.
    """
    plt.figure(figsize=(10, 6))
    
    # Sort by sample size for consistent plotting
    df_sorted = df.sort_values('n')
    
    # Plot for each test type and distribution combination
    for (dist, test_type), group in df_sorted.groupby(['distribution', 'test_type']):
        group = group.sort_values('n')
        plt.errorbar(
            group['n'], 
            group['error_rate'], 
            yerr=[[group['error_rate'] - group['ci_low']], [group['ci_high'] - group['error_rate']]],
            label=f'{dist} - {test_type}',
            capsize=5,
            marker='o'
        )
    
    plt.axhline(y=0.05, color='r', linestyle='--', label='Alpha = 0.05')
    plt.xlabel('Sample Size (n)')
    plt.ylabel('Error Rate')
    plt.title('Error Rate vs Sample Size')
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    plt.savefig(output_path, dpi=300)
    plt.close()
    
    logger.info(f"Saved plot: {output_path}")
    return output_path

def plot_comparison_all_tests(df: pd.DataFrame, output_path: str) -> str:
    """
    Generate a comparison plot of error rates across all tests for a fixed sample size range.
    
    Args:
        df: Aggregated DataFrame.
        output_path: Path to save the plot.
        
    Returns:
        Path to the saved plot.
    """
    plt.figure(figsize=(12, 7))
    
    # Select a representative sample size or range if needed, here we plot all
    # Using a line plot per test type, colored by distribution
    sns.lineplot(
        data=df, 
        x='n', 
        y='error_rate', 
        hue='test_type', 
        style='distribution',
        markers=True,
        dashes=False
    )
    
    plt.axhline(y=0.05, color='gray', linestyle='--', alpha=0.7, label='Alpha = 0.05')
    plt.xlabel('Sample Size (n)')
    plt.ylabel('Error Rate')
    plt.title('Error Rate Comparison Across Tests')
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    plt.savefig(output_path, dpi=300)
    plt.close()
    
    logger.info(f"Saved plot: {output_path}")
    return output_path

def generate_all_plots(df: pd.DataFrame, plot_dir: str) -> List[str]:
    """
    Generate all required plots and save them to the directory.
    
    Args:
        df: Aggregated DataFrame.
        plot_dir: Directory to save plots.
        
    Returns:
        List of saved file paths.
    """
    os.makedirs(plot_dir, exist_ok=True)
    plots = []
    
    if df.empty:
        logger.warning("No data to plot. Skipping plot generation.")
        return plots
    
    # Plot 1: Error Rate vs Sample Size
    path1 = os.path.join(plot_dir, 'error_rate_vs_sample_size.png')
    plots.append(plot_error_rate_vs_sample_size(df, path1))
    
    # Plot 2: Comparison All Tests
    path2 = os.path.join(plot_dir, 'comparison_all_tests.png')
    plots.append(plot_comparison_all_tests(df, path2))
    
    return plots

def main():
    """
    Main entry point for the visualizer script.
    """
    logging.basicConfig(level=logging.INFO)
    
    input_path = 'data/processed/error_rates.csv'
    output_dir = 'data/processed/plots'
    
    if not os.path.exists(input_path):
        logger.error(f"Input file not found: {input_path}")
        return
    
    df = load_aggregated_results(input_path)
    plots = generate_all_plots(df, output_dir)
    logger.info(f"Generated {len(plots)} plots.")

if __name__ == "__main__":
    main()
