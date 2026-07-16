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
