import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from typing import List, Optional, Dict, Any
import os
import logging

# Configure logger for this module
logger = logging.getLogger(__name__)

def _safe_ensure_dir(path: str) -> bool:
    """Ensure directory exists, return True if successful, False otherwise."""
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        return True
    except Exception as e:
        logger.warning(f"Failed to create directory for {path}: {e}")
        return False

def _validate_matrix(matrix: pd.DataFrame, context: str = "Input") -> bool:
    """
    Validate that the matrix is not empty and contains no NaN values.
    Returns True if valid, False otherwise. Logs warnings on failure.
    """
    if matrix is None or matrix.empty:
        logger.warning(f"{context} matrix is empty. Skipping plot generation.")
        return False
    
    if matrix.isnull().any().any():
        nan_count = matrix.isnull().sum().sum()
        logger.warning(f"{context} matrix contains {nan_count} NaN values. Skipping plot generation.")
        return False
    
    return True

def plot_heatmap(matrix: pd.DataFrame, title: str, output_path: str) -> None:
    """
    Generate a heatmap for the given matrix.
    
    Args:
        matrix: DataFrame containing the correlation matrix.
        title: Title for the plot.
        output_path: Path where the PNG file will be saved.
        
    Raises:
        ValueError: If input is invalid (empty or contains NaN).
    """
    if not _validate_matrix(matrix, f"Heatmap '{title}'"):
        return

    if not _safe_ensure_dir(output_path):
        logger.warning(f"Cannot save heatmap to {output_path} due to directory error.")
        return

    try:
        plt.figure(figsize=(10, 8))
        sns.heatmap(matrix, annot=False, cmap='coolwarm', center=0, square=True, cbar_kws={'shrink': 0.8})
        plt.title(title)
        plt.tight_layout()
        plt.savefig(output_path, dpi=300)
        plt.close()
        logger.info(f"Heatmap saved to {output_path}")
    except Exception as e:
        logger.error(f"Error generating heatmap '{title}': {e}")
        raise

def plot_histogram(null_dist: list, observed_val: float, title: str, output_path: str) -> None:
    """
    Generate a histogram of the null distribution with the observed value overlaid.
    
    Args:
        null_dist: List of values from the null distribution.
        observed_val: The observed statistic value.
        title: Title for the plot.
        output_path: Path where the PNG file will be saved.
        
    Raises:
        ValueError: If input is invalid (empty distribution or NaN).
    """
    if not null_dist:
        logger.warning(f"Null distribution for '{title}' is empty. Skipping plot generation.")
        return
    
    try:
        arr = np.array(null_dist)
        if np.isnan(arr).any():
            nan_count = np.isnan(arr).sum()
            logger.warning(f"Null distribution for '{title}' contains {nan_count} NaN values. Skipping plot generation.")
            return
        
        if not _safe_ensure_dir(output_path):
            logger.warning(f"Cannot save histogram to {output_path} due to directory error.")
            return

        plt.figure(figsize=(10, 6))
        sns.histplot(arr, kde=True, color='skyblue', edgecolor='black', stat='density')
        plt.axvline(x=observed_val, color='red', linestyle='--', linewidth=2, label=f'Observed: {observed_val:.4f}')
        plt.title(title)
        plt.xlabel('Value')
        plt.ylabel('Density')
        plt.legend()
        plt.tight_layout()
        plt.savefig(output_path, dpi=300)
        plt.close()
        logger.info(f"Histogram saved to {output_path}")
    except Exception as e:
        logger.error(f"Error generating histogram '{title}': {e}")
        raise

def plot_primary_threshold_visualizations(corr_matrix: pd.DataFrame, 
                                          null_dist_stats: Dict[str, Any], 
                                          threshold: float, 
                                          output_dir: str) -> None:
    """
    Generate primary threshold visualizations (heatmap and histogram).
    
    Args:
        corr_matrix: Observed correlation matrix.
        null_dist_stats: Dictionary containing null distribution statistics.
        threshold: The correlation threshold used.
        output_dir: Directory to save plots.
    """
    if not _validate_matrix(corr_matrix, f"Primary Threshold {threshold} Matrix"):
        return

    os.makedirs(output_dir, exist_ok=True)
    
    heatmap_path = os.path.join(output_dir, f"primary_heatmap_threshold_{threshold}.png")
    histogram_path = os.path.join(output_dir, f"primary_histogram_threshold_{threshold}.png")
    
    # Plot Heatmap
    try:
        plot_heatmap(corr_matrix, f"Observed Correlation Matrix (|r| > {threshold})", heatmap_path)
    except Exception as e:
        logger.error(f"Failed to generate primary heatmap: {e}")
    
    # Plot Histogram for Mean Absolute Correlation
    if 'mean_abs_corr' in null_dist_stats and 'observed_mean_abs_corr' in null_dist_stats:
        try:
            plot_histogram(
                null_dist_stats['mean_abs_corr'],
                null_dist_stats['observed_mean_abs_corr'],
                f"Distribution of Mean Absolute Correlation (Threshold: {threshold})",
                histogram_path
            )
        except Exception as e:
            logger.error(f"Failed to generate primary histogram: {e}")

def plot_sensitivity_sweep(results_df: pd.DataFrame, output_path: str) -> None:
    """
    Plot sensitivity analysis results (significant counts vs threshold).
    
    Args:
        results_df: DataFrame with threshold and significant counts.
        output_path: Path to save the plot.
    """
    if results_df is None or results_df.empty:
        logger.warning("Sensitivity results DataFrame is empty. Skipping plot generation.")
        return

    if 'threshold' not in results_df.columns or 'significant_count' not in results_df.columns:
        logger.warning("Sensitivity results DataFrame missing required columns. Skipping plot generation.")
        return

    if results_df['threshold'].isnull().any() or results_df['significant_count'].isnull().any():
        logger.warning("Sensitivity results contain NaN values. Skipping plot generation.")
        return

    if not _safe_ensure_dir(output_path):
        logger.warning(f"Cannot save sensitivity plot to {output_path} due to directory error.")
        return

    try:
        plt.figure(figsize=(10, 6))
        plt.plot(results_df['threshold'], results_df['significant_count'], marker='o', linestyle='-', color='blue')
        plt.title('Sensitivity Analysis: Significant Edge Count vs Threshold')
        plt.xlabel('Threshold (|r|)')
        plt.ylabel('Significant Edge Count')
        plt.grid(True, which='both', linestyle='--', alpha=0.7)
        plt.tight_layout()
        plt.savefig(output_path, dpi=300)
        plt.close()
        logger.info(f"Sensitivity plot saved to {output_path}")
    except Exception as e:
        logger.error(f"Error generating sensitivity plot: {e}")
        raise

def plot_observed_vs_null_heatmap(observed_matrix: pd.DataFrame, 
                                  null_mean_matrix: pd.DataFrame, 
                                  output_path: str) -> None:
    """
    Plot a heatmap comparing observed correlations to the mean of the null distribution.
    
    Args:
        observed_matrix: Observed correlation matrix.
        null_mean_matrix: Mean correlation matrix from null distribution.
        output_path: Path to save the plot.
    """
    if not _validate_matrix(observed_matrix, "Observed vs Null - Observed"):
        return
    if not _validate_matrix(null_mean_matrix, "Observed vs Null - Null Mean"):
        return

    if observed_matrix.shape != null_mean_matrix.shape:
        logger.warning("Observed and Null matrices have different shapes. Skipping plot.")
        return

    if not _safe_ensure_dir(output_path):
        logger.warning(f"Cannot save comparison heatmap to {output_path} due to directory error.")
        return

    try:
        diff_matrix = observed_matrix - null_mean_matrix
        plt.figure(figsize=(10, 8))
        sns.heatmap(diff_matrix, annot=False, cmap='RdBu_r', center=0, square=True, cbar_kws={'shrink': 0.8})
        plt.title('Difference: Observed Correlation - Null Mean')
        plt.tight_layout()
        plt.savefig(output_path, dpi=300)
        plt.close()
        logger.info(f"Observed vs Null heatmap saved to {output_path}")
    except Exception as e:
        logger.error(f"Error generating observed vs null heatmap: {e}")
        raise

def plot_sensitivity_results(results_df: pd.DataFrame, output_path: str) -> None:
    """
    Generate a comprehensive sensitivity results plot (bar chart of significant counts).
    
    Args:
        results_df: DataFrame with sensitivity analysis results.
        output_path: Path to save the plot.
    """
    if results_df is None or results_df.empty:
        logger.warning("Sensitivity results DataFrame is empty. Skipping plot generation.")
        return

    if 'threshold' not in results_df.columns or 'significant_count' not in results_df.columns:
        logger.warning("Sensitivity results DataFrame missing required columns. Skipping plot generation.")
        return

    if results_df['threshold'].isnull().any() or results_df['significant_count'].isnull().any():
        logger.warning("Sensitivity results contain NaN values. Skipping plot generation.")
        return

    if not _safe_ensure_dir(output_path):
        logger.warning(f"Cannot save sensitivity results plot to {output_path} due to directory error.")
        return

    try:
        plt.figure(figsize=(10, 6))
        sns.barplot(x='threshold', y='significant_count', data=results_df, palette='viridis')
        plt.title('Significant Edge Counts Across Thresholds')
        plt.xlabel('Threshold (|r|)')
        plt.ylabel('Significant Edge Count')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(output_path, dpi=300)
        plt.close()
        logger.info(f"Sensitivity results plot saved to {output_path}")
    except Exception as e:
        logger.error(f"Error generating sensitivity results plot: {e}")
        raise