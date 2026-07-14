"""
Visualizer module for generating publication-ready plots from aggregated results.

This module handles all visualization logic, separating it from the aggregation
logic in analyzer.py as per task T032b.
"""
import os
import logging
from typing import Optional, List, Dict, Any
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for script execution
import matplotlib.pyplot as plt
import seaborn as sns
from analyzer import load_simulation_results, aggregate_results

logger = logging.getLogger(__name__)

# Set style for publication-ready plots
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

def load_aggregated_results(file_path: str) -> pd.DataFrame:
    """
    Load aggregated results from a CSV file.
    
    Args:
        file_path: Path to the aggregated results CSV.
        
    Returns:
        DataFrame with aggregated results.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Aggregated results file not found: {file_path}")
    
    logger.info(f"Loading aggregated results from {file_path}")
    return pd.read_csv(file_path)

def plot_error_rate_vs_sample_size(df: pd.DataFrame, output_path: str) -> None:
    """
    Generate a plot of Error Rate vs. Sample Size with confidence intervals.
    
    Args:
        df: DataFrame with aggregated results (must include error_rate, ci_lower, ci_upper).
        output_path: Path to save the plot.
    """
    logger.info(f"Generating Error Rate vs. Sample Size plot: {output_path}")
    
    plt.figure(figsize=(10, 6))
    
    # Plot each test type and distribution combination
    for (test_type, distribution), group in df.groupby(['test_type', 'distribution']):
        group = group.sort_values('sample_size')
        
        plt.errorbar(
            group['sample_size'],
            group['error_rate'],
            yerr=[group['error_rate'] - group['ci_lower'], group['ci_upper'] - group['error_rate']],
            label=f"{test_type} ({distribution})",
            capsize=5,
            marker='o',
            linestyle='-'
        )
    
    plt.axhline(y=0.05, color='r', linestyle='--', label='Alpha (0.05)', linewidth=1)
    
    plt.xlabel('Sample Size (n)')
    plt.ylabel('Error Rate')
    plt.title('Error Rate vs. Sample Size by Test and Distribution')
    plt.legend(title='Test / Distribution')
    plt.xscale('log')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Plot saved to {output_path}")

def plot_comparison_all_tests(df: pd.DataFrame, output_path: str) -> None:
    """
    Generate a comparison plot showing all tests side-by-side for a given distribution.
    
    Args:
        df: DataFrame with aggregated results.
        output_path: Path to save the plot.
    """
    logger.info(f"Generating comparison plot: {output_path}")
    
    distributions = df['distribution'].unique()
    
    fig, axes = plt.subplots(1, len(distributions), figsize=(4 * len(distributions), 6), sharey=True)
    if len(distributions) == 1:
        axes = [axes]
    
    for idx, distribution in enumerate(distributions):
        sub_df = df[df['distribution'] == distribution]
        
        for test_type in sub_df['test_type'].unique():
            test_df = sub_df[sub_df['test_type'] == test_type].sort_values('sample_size')
            
            axes[idx].errorbar(
                test_df['sample_size'],
                test_df['error_rate'],
                yerr=[test_df['error_rate'] - test_df['ci_lower'], test_df['ci_upper'] - test_df['error_rate']],
                label=test_type,
                capsize=3,
                marker='o',
                linestyle='-'
            )
        
        axes[idx].axhline(y=0.05, color='r', linestyle='--', alpha=0.5)
        axes[idx].set_title(f'Distribution: {distribution}')
        axes[idx].set_xlabel('Sample Size (n)')
        if idx == 0:
            axes[idx].set_ylabel('Error Rate')
        axes[idx].set_xscale('log')
        axes[idx].legend(fontsize=8)
    
    plt.suptitle('Error Rate Comparison Across Tests by Distribution', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Comparison plot saved to {output_path}")

def generate_all_plots(aggregated_df: pd.DataFrame, output_dir: str) -> List[str]:
    """
    Generate all publication-ready plots and save them to the output directory.
    
    Args:
        aggregated_df: DataFrame with aggregated results.
        output_dir: Directory to save the plots.
        
    Returns:
        List of paths to the generated plot files.
    """
    os.makedirs(output_dir, exist_ok=True)
    generated_files = []
    
    # Plot 1: Error Rate vs. Sample Size (all)
    plot1_path = os.path.join(output_dir, 'error_rate_vs_sample_size.png')
    plot_error_rate_vs_sample_size(aggregated_df, plot1_path)
    generated_files.append(plot1_path)
    
    # Plot 2: Comparison by distribution
    plot2_path = os.path.join(output_dir, 'comparison_by_distribution.png')
    plot_comparison_all_tests(aggregated_df, plot2_path)
    generated_files.append(plot2_path)
    
    logger.info(f"Generated {len(generated_files)} plots in {output_dir}")
    return generated_files

def main():
    """
    Main entry point for the visualizer script.
    Loads aggregated results and generates all plots.
    """
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    input_path = 'data/processed/error_rates.csv'
    output_dir = 'data/processed/plots'
    
    if not os.path.exists(input_path):
        logger.error(f"Input file not found: {input_path}")
        logger.error("Please run the analyzer first to generate the aggregated results.")
        return
    
    df = load_aggregated_results(input_path)
    generate_all_plots(df, output_dir)
    
    logger.info("Visualization complete.")

if __name__ == "__main__":
    main()
