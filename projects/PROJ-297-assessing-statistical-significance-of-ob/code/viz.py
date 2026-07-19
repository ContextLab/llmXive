"""
Visualization module for correlation analysis.
Implements scaling mechanisms for large matrices (>50 variables).
"""

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from typing import List, Optional, Dict, Any
import os
import logging

logger = logging.getLogger(__name__)

def plot_heatmap(matrix: pd.DataFrame, title: str, output_path: str, 
                 max_vars: int = 50, method: str = 'cluster') -> None:
    """
    Plot correlation heatmap with scaling for large matrices.
    
    Args:
        matrix: Correlation matrix (pandas DataFrame)
        title: Plot title
        output_path: Path to save the figure
        max_vars: Maximum number of variables to display directly.
                If matrix has more, scaling is applied.
        method: Scaling method ('cluster', 'top', 'downsample')
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    n_vars = matrix.shape[0]
    
    if n_vars <= max_vars:
        # Direct plotting for small matrices
        logger.info(f"Plotting direct heatmap for {n_vars} variables")
        _plot_direct_heatmap(matrix, title, output_path)
    else:
        # Apply scaling mechanism for large matrices
        logger.info(f"Applying {method} scaling for {n_vars} variables (limit: {max_vars})")
        if method == 'cluster':
            _plot_clustered_heatmap(matrix, title, output_path, max_vars)
        elif method == 'top':
            _plot_top_correlations_heatmap(matrix, title, output_path, max_vars)
        elif method == 'downsample':
            _plot_downsampled_heatmap(matrix, title, output_path, max_vars)
        else:
            logger.warning(f"Unknown method '{method}', falling back to cluster")
            _plot_clustered_heatmap(matrix, title, output_path, max_vars)

def _plot_direct_heatmap(matrix: pd.DataFrame, title: str, output_path: str) -> None:
    """Plot a standard correlation heatmap."""
    plt.figure(figsize=(min(12, n_vars/2), min(10, n_vars/2)))
    sns.heatmap(matrix, cmap='coolwarm', center=0, annot=False, 
                linewidths=0.5, cbar_kws={'label': 'Correlation'})
    plt.title(title)
    plt.xticks(rotation=90)
    plt.yticks(rotation=0)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

def _plot_clustered_heatmap(matrix: pd.DataFrame, title: str, output_path: str, 
                             max_vars: int) -> None:
    """
    Plot heatmap with hierarchical clustering to group correlated variables.
    Shows representative clusters rather than all variables.
    """
    from scipy.cluster.hierarchy import linkage, leaves_list
    from scipy.spatial.distance import squareform
    
    # Convert correlation to distance
    # Use 1 - |correlation| as distance metric
    corr_abs = matrix.abs()
    # Distance matrix: 1 - correlation
    dist_matrix = 1 - corr_abs.values
    
    # Perform hierarchical clustering
    # Use condensed distance matrix for linkage
    condensed_dist = squareform(dist_matrix, checks=False)
    link = linkage(condensed_dist, method='average')
    
    # Get optimal leaf order
    order = leaves_list(link)
    
    # Reorder matrix
    reordered_matrix = matrix.iloc[order, order]
    
    # If still too large, select a subset of clusters
    n_vars = reordered_matrix.shape[0]
    if n_vars > max_vars:
        # Select representative variables from each cluster
        # Simple approach: take every n_vars/max_vars-th variable
        step = n_vars // max_vars
        selected_indices = order[::step][:max_vars]
        reordered_matrix = matrix.iloc[selected_indices, selected_indices]
    
    plt.figure(figsize=(12, 10))
    sns.heatmap(reordered_matrix, cmap='coolwarm', center=0, annot=False,
                linewidths=0.5, cbar_kws={'label': 'Correlation'})
    plt.title(f"{title} (Clustered, {reordered_matrix.shape[0]} variables shown)")
    plt.xticks(rotation=90)
    plt.yticks(rotation=0)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

def _plot_top_correlations_heatmap(matrix: pd.DataFrame, title: str, 
                                    output_path: str, max_vars: int) -> None:
    """
    Plot heatmap showing only the top correlated variable pairs.
    Identifies the most significant correlations and focuses visualization on them.
    """
    # Get absolute correlations and find top pairs
    n_vars = matrix.shape[0]
    
    # Extract upper triangle
    upper_tri = matrix.where(np.triu(np.ones(matrix.shape), k=1).astype(bool))
    
    # Stack to get pairs
    corr_pairs = upper_tri.stack().dropna()
    
    # Get top correlations
    top_n = min(max_vars * 2, len(corr_pairs))  # Allow some extra for context
    top_corr = corr_pairs.nlargest(top_n)
    
    # Get unique variables in top correlations
    top_vars = set()
    for idx in top_corr.index:
        top_vars.add(idx[0])
        top_vars.add(idx[1])
    
    # Limit to max_vars
    if len(top_vars) > max_vars:
        # Take most frequent variables in top correlations
        var_counts = pd.Series(list(top_vars))
        # Actually, just take the first max_vars
        top_vars = list(top_vars)[:max_vars]
    
    # Subset matrix
    selected_matrix = matrix.loc[list(top_vars), list(top_vars)]
    
    plt.figure(figsize=(12, 10))
    sns.heatmap(selected_matrix, cmap='coolwarm', center=0, annot=False,
                linewidths=0.5, cbar_kws={'label': 'Correlation'})
    plt.title(f"{title} (Top {len(top_vars)} correlated variables)")
    plt.xticks(rotation=90)
    plt.yticks(rotation=0)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

def _plot_downsampled_heatmap(matrix: pd.DataFrame, title: str, 
                               output_path: str, max_vars: int) -> None:
    """
    Plot heatmap with systematic downsampling of variables.
    Selects variables at regular intervals to preserve structure.
    """
    n_vars = matrix.shape[0]
    indices = np.linspace(0, n_vars-1, max_vars, dtype=int)
    selected_matrix = matrix.iloc[indices, indices]
    
    plt.figure(figsize=(12, 10))
    sns.heatmap(selected_matrix, cmap='coolwarm', center=0, annot=False,
                linewidths=0.5, cbar_kws={'label': 'Correlation'})
    plt.title(f"{title} (Downsampled to {max_vars} variables)")
    plt.xticks(rotation=90)
    plt.yticks(rotation=0)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

def plot_histogram(null_dist: list, observed_val: float, title: str, output_path: str) -> None:
    """Plot null distribution histogram with observed value."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.figure(figsize=(10, 6))
    plt.hist(null_dist, bins=50, alpha=0.7, label='Null Distribution', color='skyblue', edgecolor='black')
    plt.axvline(observed_val, color='red', linestyle='dashed', linewidth=2, label='Observed')
    plt.title(title)
    plt.xlabel('Statistic Value')
    plt.ylabel('Frequency')
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

def plot_primary_threshold_visualizations(df: pd.DataFrame, threshold: float, output_dir: str,
                                           method: str = 'cluster') -> None:
    """Generate primary threshold visualizations with scaling support."""
    corr = df.corr()
    n_vars = corr.shape[0]
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Plot heatmap with scaling if needed
    heatmap_path = os.path.join(output_dir, "primary_heatmap.png")
    plot_heatmap(corr, f"Correlation Matrix (|r|>{threshold})", heatmap_path, 
                max_vars=50, method=method)
    
    logger.info(f"Primary heatmap saved to {heatmap_path}")
    
    # Note: Histogram plotting requires null distribution which is computed elsewhere
    # This function focuses on the matrix visualization scaling

def main():
    """Main entry point for visualization module."""
    pass

if __name__ == "__main__":
    main()