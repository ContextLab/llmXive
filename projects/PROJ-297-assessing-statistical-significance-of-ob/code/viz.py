"""Visualization module for statistical analysis results.

Provides functions for generating heatmaps, histograms, and other
visualizations to support the analysis pipeline.
"""
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from typing import List, Optional, Dict, Any
import os


def plot_heatmap(
    matrix: pd.DataFrame, title: str, output_path: str
) -> None:
    """Generate and save a heatmap of a correlation matrix.

    Args:
        matrix: Correlation matrix to visualize.
        title: Title for the plot.
        output_path: Path to save the PNG file.
    """
    plt.figure(figsize=(12, 10))
    sns.heatmap(matrix, annot=False, cmap="coolwarm", center=0, linewidths=0.5)
    plt.title(title)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()


def plot_histogram(
    null_dist: List[float], observed_val: float, title: str, output_path: str
) -> None:
    """Generate and save a histogram of a null distribution with observed value.

    Args:
        null_dist: List of values from the null distribution.
        observed_val: Observed statistic value to overlay.
        title: Title for the plot.
        output_path: Path to save the PNG file.
    """
    plt.figure(figsize=(10, 6))
    sns.histplot(null_dist, kde=True, stat="density", bins=30, alpha=0.7, label="Null Distribution")
    plt.axvline(x=observed_val, color='red', linestyle='--', linewidth=2, label=f"Observed ({observed_val:.3f})")
    plt.title(title)
    plt.xlabel("Statistic Value")
    plt.ylabel("Density")
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()


def plot_primary_threshold_visualizations(
    corr_matrix: pd.DataFrame,
    null_dist: Dict[str, List[float]],
    observed_stats: Dict[str, float],
    output_dir: str,
) -> None:
    """Generate primary threshold visualizations.

    Args:
        corr_matrix: Observed correlation matrix.
        null_dist: Dictionary of null distributions.
        observed_stats: Dictionary of observed statistics.
        output_dir: Directory to save the plots.
    """
    os.makedirs(output_dir, exist_ok=True)

    # Heatmap
    heatmap_path = os.path.join(output_dir, "primary_correlation_heatmap.png")
    plot_heatmap(corr_matrix, "Primary Threshold Correlation Heatmap (|r| > 0.3)", heatmap_path)

    # Histograms for each statistic
    for stat_name, observed_val in observed_stats.items():
        hist_path = os.path.join(output_dir, f"primary_{stat_name}_histogram.png")
        plot_histogram(
            null_dist[stat_name],
            observed_val,
            f"Null Distribution for {stat_name} (Primary Threshold)",
            hist_path,
        )


def plot_sensitivity_sweep(
    sensitivity_data: List[Dict[str, Any]], output_path: str
) -> None:
    """Generate a plot for sensitivity sweep results.

    Args:
        sensitivity_data: List of dictionaries with threshold and significant count.
        output_path: Path to save the plot.
    """
    thresholds = [d["threshold"] for d in sensitivity_data]
    significant_counts = [d["significant_count"] for d in sensitivity_data]

    plt.figure(figsize=(10, 6))
    plt.plot(thresholds, significant_counts, marker='o', linestyle='-', color='b')
    plt.xlabel("Correlation Threshold")
    plt.ylabel("Significant Edge Count")
    plt.title("Sensitivity Analysis: Significant Edges vs Threshold")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()


def plot_observed_vs_null_heatmap(
    observed_matrix: pd.DataFrame,
    null_mean_matrix: pd.DataFrame,
    output_path: str,
) -> None:
    """Generate a heatmap comparing observed and null mean correlations.

    Args:
        observed_matrix: Observed correlation matrix.
        null_mean_matrix: Mean of null distribution correlation matrices.
        output_path: Path to save the plot.
    """
    diff_matrix = observed_matrix - null_mean_matrix

    plt.figure(figsize=(12, 10))
    sns.heatmap(diff_matrix, annot=False, cmap="RdBu_r", center=0, linewidths=0.5)
    plt.title("Difference: Observed Correlation - Null Mean Correlation")
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()


def plot_sensitivity_results(
    sensitivity_results: Dict[str, List[Dict[str, Any]]],
    output_path: str,
    title: str = "Sensitivity Analysis: Significant Findings vs Threshold"
) -> None:
    """Generate a line plot showing significant findings vs correlation threshold for all datasets.

    This function aggregates sensitivity analysis results across multiple datasets
    and produces a multi-line plot to visualize robustness of findings across thresholds.
    As required by FR-005, this provides a visual summary of how significance counts
    change with correlation thresholds.

    Args:
        sensitivity_results: Dictionary mapping dataset_id to list of sensitivity data.
            Each sensitivity data entry must contain 'threshold' and 'significant_count'.
        output_path: Path to save the output PNG file.
        title: Title for the plot.
    """
    if not sensitivity_results:
        raise ValueError("sensitivity_results cannot be empty")

    plt.figure(figsize=(12, 8))

    # Extract unique thresholds from all datasets to ensure consistent x-axis
    all_thresholds = set()
    for dataset_data in sensitivity_results.values():
        for entry in dataset_data:
            all_thresholds.add(entry["threshold"])
    
    sorted_thresholds = sorted(list(all_thresholds))

    # Plot a line for each dataset
    for dataset_id, data in sensitivity_results.items():
        # Create a mapping from threshold to significant count
        threshold_map = {entry["threshold"]: entry["significant_count"] for entry in data}
        
        # Get values for all thresholds (fill with 0 if not present)
        y_values = [threshold_map.get(t, 0) for t in sorted_thresholds]
        
        plt.plot(
            sorted_thresholds, 
            y_values, 
            marker='o', 
            linestyle='-', 
            label=dataset_id,
            alpha=0.8
        )

    plt.xlabel("Correlation Threshold (|r|)", fontsize=12)
    plt.ylabel("Number of Significant Findings", fontsize=12)
    plt.title(title, fontsize=14, fontweight='bold')
    plt.legend(title="Dataset", bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.grid(True, alpha=0.3, linestyle='--')
    plt.xticks(sorted_thresholds)
    
    # Ensure x-axis shows all thresholds clearly
    if len(sorted_thresholds) > 1:
        plt.xlim(sorted_thresholds[0] - 0.02, sorted_thresholds[-1] + 0.02)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()