"""
Visualization module for T028: Coverage vs Epsilon plots.

Generates line plots of coverage vs. epsilon with error bars (SE) for Laplace and Gaussian noise.
Output: artifacts/coverage_vs_epsilon.png

Dependencies:
- T013c (coverage_results.csv)
- T026 (GLM analysis - optional for context, but not required for plotting)
"""

import os
import sys
import logging
import json
from pathlib import Path
from typing import Tuple, Optional, Dict, Any, List

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Import config for paths
from config import get_artifact_path, get_figure_path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
COVERAGE_RESULTS_FILE = "coverage_results.csv"
OUTPUT_PNG = "coverage_vs_epsilon.png"
TARGET_COVERAGE = 0.95  # Nominal coverage target

def load_coverage_data() -> pd.DataFrame:
    """
    Load coverage results from artifacts/coverage_results.csv.
    
    Returns:
        pd.DataFrame: The loaded coverage results.
        
    Raises:
        FileNotFoundError: If the results file does not exist.
        ValueError: If the file is empty or missing required columns.
    """
    file_path = get_artifact_path(COVERAGE_RESULTS_FILE)
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Results file not found at {file_path}. "
                              "Did you run the main simulation (T013a/T042)?")
    
    df = pd.read_csv(file_path)
    
    required_cols = ['dataset', 'epsilon', 'noise_type', 'statistic', 'coverage_rate', 'seed']
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        raise ValueError(f"Missing required columns in {file_path}: {missing_cols}")
    
    if df.empty:
        raise ValueError(f"Results file {file_path} is empty. No data to plot.")
    
    logger.info(f"Loaded {len(df)} rows from {file_path}")
    return df

def aggregate_coverage_stats(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate coverage rates by dataset, epsilon, noise_type, and statistic.
    Calculates mean coverage and standard error (SE).
    
    Args:
        df: Raw coverage results DataFrame.
        
    Returns:
        pd.DataFrame: Aggregated statistics with columns:
            dataset, epsilon, noise_type, statistic, 
            coverage_rate (mean), se_coverage (std/sqrt(n)), n_samples
    """
    # Group by the relevant dimensions
    grouped = df.groupby(['dataset', 'epsilon', 'noise_type', 'statistic'])['coverage_rate'].agg(
        coverage_rate='mean',
        se_coverage=lambda x: x.std() / np.sqrt(len(x)),
        n_samples='count'
    ).reset_index()
    
    logger.info(f"Aggregated to {len(grouped)} unique conditions")
    return grouped

def plot_coverage_vs_epsilon(
    df_agg: pd.DataFrame,
    target_coverage: float = TARGET_COVERAGE,
    figsize: Tuple[int, int] = (12, 8)
) -> plt.Figure:
    """
    Generate line plots of coverage vs. epsilon with error bars.
    
    Creates a separate subplot for each dataset, plotting coverage rate against epsilon.
    Separate lines/markers for Laplace and Gaussian noise.
    Error bars represent Standard Error (SE).
    
    Args:
        df_agg: Aggregated coverage statistics DataFrame.
        target_coverage: The nominal coverage target line (default 0.95).
        figsize: Figure size (width, height) in inches.
        
    Returns:
        plt.Figure: The matplotlib figure object.
    """
    # Get unique datasets
    datasets = df_agg['dataset'].unique()
    n_datasets = len(datasets)
    
    if n_datasets == 0:
        raise ValueError("No datasets found in aggregated data.")
    
    # Create subplots
    fig, axes = plt.subplots(1, n_datasets, figsize=figsize, sharey=True)
    if n_datasets == 1:
        axes = [axes]  # Ensure iterable
    
    # Define styles for noise types
    noise_styles = {
        'Laplace': {'color': '#1f77b4', 'marker': 'o', 'linestyle': '-', 'label': 'Laplace'},
        'Gaussian': {'color': '#ff7f0e', 'marker': 's', 'linestyle': '--', 'label': 'Gaussian'}
    }
    
    for i, dataset in enumerate(datasets):
        ax = axes[i]
        subset = df_agg[df_agg['dataset'] == dataset]
        
        # Sort by epsilon for line plotting
        subset = subset.sort_values('epsilon')
        
        # Plot for each statistic (e.g., mean, regression)
        # For simplicity, we'll plot the 'mean' statistic if available, otherwise all
        statistics = subset['statistic'].unique()
        
        for stat in statistics:
            stat_subset = subset[subset['statistic'] == stat]
            
            # Filter for noise types we have styles for
            for noise_type, style in noise_styles.items():
                noise_data = stat_subset[stat_subset['noise_type'] == noise_type]
                
                if noise_data.empty:
                    continue
                
                # Sort by epsilon
                noise_data = noise_data.sort_values('epsilon')
                
                # Plot line with error bars
                ax.errorbar(
                    noise_data['epsilon'],
                    noise_data['coverage_rate'],
                    yerr=noise_data['se_coverage'],
                    label=f"{style['label']} ({stat})",
                    color=style['color'],
                    marker=style['marker'],
                    linestyle=style['linestyle'],
                    capsize=4,
                    markersize=6,
                    linewidth=2
                )
        
        # Add target coverage line
        ax.axhline(y=target_coverage, color='gray', linestyle=':', alpha=0.7, label=f"Target ({target_coverage})")
        
        ax.set_xlabel(r'$\epsilon$ (Privacy Budget)')
        ax.set_title(f'{dataset.capitalize()} Dataset')
        ax.grid(True, alpha=0.3)
        ax.set_xlim(left=0)
        
        # Set y-axis limits to cover reasonable coverage range
        ax.set_ylim(bottom=0.8, top=1.05)
        
        if i == 0:
            ax.set_ylabel('Empirical Coverage Rate')
            ax.legend(loc='lower right', fontsize=8)
        else:
            # Hide legend for subsequent plots to reduce clutter
            pass
    
    plt.suptitle('Empirical Coverage vs. Differential Privacy Budget ($\epsilon$)', fontsize=14, y=1.02)
    plt.tight_layout()
    
    return fig

def main():
    """
    Main entry point for T028.
    Loads coverage results, aggregates stats, and saves the plot.
    """
    logger.info("Starting T028: Coverage vs Epsilon Visualization")
    
    try:
        # 1. Load data
        df_raw = load_coverage_data()
        
        # 2. Aggregate statistics
        df_agg = aggregate_coverage_stats(df_raw)
        
        # 3. Generate plot
        fig = plot_coverage_vs_epsilon(df_agg)
        
        # 4. Save figure
        output_path = get_artifact_path(OUTPUT_PNG)
        fig.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close(fig)
        
        logger.info(f"Successfully saved plot to {output_path}")
        
        # Verify file exists and has content
        if not os.path.exists(output_path):
            raise RuntimeError(f"Failed to write output file: {output_path}")
        
        file_size = os.path.getsize(output_path)
        if file_size == 0:
            raise RuntimeError(f"Output file is empty: {output_path}")
        
        logger.info(f"Output file size: {file_size} bytes")
        
    except FileNotFoundError as e:
        logger.error(f"Data file error: {e}")
        raise
    except ValueError as e:
        logger.error(f"Data validation error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during plotting: {e}")
        raise

if __name__ == "__main__":
    main()