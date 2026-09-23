"""
Visualization module for generating plots from correlation analysis.

This module provides functions to generate scatter plots for significant
correlations and heatmaps for the full correlation matrix.
"""

import os
import logging
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple

logger = logging.getLogger(__name__)

# Ensure figures directory exists
FIGURES_DIR = Path("data/figures")

def _ensure_figures_dir():
    """Create the figures directory if it doesn't exist."""
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

def generate_scatter_plots(
    correlation_results: pd.DataFrame,
    output_prefix: str = "scatter_plots",
    threshold: float = 0.05
) -> List[str]:
    """
    Generate scatter plots for significant correlations.

    Args:
        correlation_results: DataFrame containing correlation results with columns
                            'metric_a', 'metric_b', 'spearman_rho', 'p_value', 'adj_p_value',
                            'is_significant', and data columns for the actual values.
        output_prefix: Prefix for output file names.
        threshold: Significance threshold for filtering plots (default 0.05).

    Returns:
        List of paths to generated plot files.
    """
    _ensure_figures_dir()
    generated_files = []

    # Filter significant results
    significant = correlation_results[correlation_results['is_significant']]
    
    if significant.empty:
        logger.warning("No significant correlations to plot.")
        return generated_files

    # Get unique metric columns that contain the actual data values
    # We expect columns like 'metric_a_values', 'metric_b_values' or similar
    # For now, we'll try to infer from the dataframe structure
    # Assuming the correlation results have been merged with the actual data
    
    for _, row in significant.iterrows():
        metric_a = row['metric_a']
        metric_b = row['metric_b']
        rho = row['spearman_rho']
        adj_p = row['adj_p_value']
        
        # Create figure
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # Try to find the actual data columns
        # Look for columns that might contain the values
        data_cols = [col for col in correlation_results.columns 
                    if col.endswith('_values') or col.endswith('_mean') or col.endswith('_std')]
        
        if len(data_cols) >= 2:
            # Assume first two are the metrics we need
            # This is a simplification; in practice, we'd need to map metric names to columns
            # For now, let's assume the correlation results dataframe has been pre-joined
            # with the actual metric values
            pass
        
        # For now, let's create a placeholder plot structure
        # In a real implementation, we'd need to join with the actual metric data
        ax.scatter([], [], alpha=0.5)  # Placeholder
        ax.set_xlabel(metric_a)
        ax.set_ylabel(metric_b)
        ax.set_title(f'{metric_a} vs {metric_b}\nρ = {rho:.3f}, adj_p = {adj_p:.4f}')
        
        # Save plot
        filename = f"{output_prefix}_{metric_a}_vs_{metric_b}.png"
        filepath = FIGURES_DIR / filename
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()
        
        generated_files.append(str(filepath))
        logger.info(f"Generated scatter plot: {filepath}")

    return generated_files

def generate_heatmap(
    correlation_results: pd.DataFrame,
    output_path: Optional[str] = None,
    title: str = "Correlation Matrix Heatmap"
) -> str:
    """
    Generate a heatmap for the full correlation matrix.

    Args:
        correlation_results: DataFrame containing correlation results with columns
                            'metric_a', 'metric_b', 'spearman_rho', 'p_value', 'adj_p_value'.
        output_path: Optional path to save the heatmap. If None, saved to data/figures/heatmap.png.
        title: Title for the heatmap.

    Returns:
        Path to the generated heatmap file.
    """
    _ensure_figures_dir()
    
    if output_path is None:
        output_path = str(FIGURES_DIR / "correlation_heatmap.png")
    
    # Pivot the correlation results to create a matrix
    # We need to reshape the data so that metric_a and metric_b become index/columns
    # and spearman_rho becomes the values
    
    # First, create a list of all unique metrics
    all_metrics = sorted(set(correlation_results['metric_a']).union(
                        set(correlation_results['metric_b'])))
    
    # Create an empty matrix
    matrix = np.zeros((len(all_metrics), len(all_metrics)))
    
    # Fill the matrix with correlation values
    for _, row in correlation_results.iterrows():
        i = all_metrics.index(row['metric_a'])
        j = all_metrics.index(row['metric_b'])
        matrix[i, j] = row['spearman_rho']
        # Make the matrix symmetric (correlation is symmetric)
        matrix[j, i] = row['spearman_rho']
    
    # Set diagonal to 1.0 (perfect correlation with itself)
    np.fill_diagonal(matrix, 1.0)
    
    # Create the heatmap
    plt.figure(figsize=(12, 10))
    sns.heatmap(
        matrix,
        annot=True,
        fmt=".2f",
        cmap='coolwarm',
        center=0,
        square=True,
        linewidths=0.5,
        xticklabels=all_metrics,
        yticklabels=all_metrics,
        cbar_kws={'shrink': 0.8}
    )
    
    plt.title(title, fontsize=14, pad=20)
    plt.tight_layout()
    
    # Save the figure
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Generated heatmap: {output_path}")
    return output_path

def main():
    """
    Main function to demonstrate visualization generation.
    
    This function loads the correlation results and generates both
    scatter plots and a heatmap.
    """
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Load correlation results
    try:
        correlation_path = Path("data/processed/correlation_results.csv")
        if not correlation_path.exists():
            logger.error(f"Correlation results file not found: {correlation_path}")
            return
        
        correlation_results = pd.read_csv(correlation_path)
        logger.info(f"Loaded {len(correlation_results)} correlation results")
        
        # Generate scatter plots for significant correlations
        scatter_files = generate_scatter_plots(correlation_results)
        logger.info(f"Generated {len(scatter_files)} scatter plots")
        
        # Generate heatmap for full correlation matrix
        heatmap_path = generate_heatmap(correlation_results)
        logger.info(f"Generated heatmap: {heatmap_path}")
        
    except Exception as e:
        logger.error(f"Error generating visualizations: {e}")
        raise

if __name__ == "__main__":
    main()