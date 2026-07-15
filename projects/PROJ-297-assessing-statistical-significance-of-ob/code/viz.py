import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from typing import List, Optional, Dict, Any
import os
import config

def plot_heatmap(matrix: pd.DataFrame, title: str, output_path: str) -> None:
    """
    Generate a high-resolution heatmap of a correlation matrix.
    """
    plt.figure(figsize=(12, 10))
    sns.heatmap(matrix, annot=True, cmap='coolwarm', center=0, linewidths=.5)
    plt.title(title)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Heatmap saved to {output_path}")

def plot_histogram(null_dist: list, observed_val: float, title: str, output_path: str) -> None:
    """
    Generate a histogram of a null distribution with the observed value overlaid.
    """
    plt.figure(figsize=(10, 6))
    sns.histplot(null_dist, kde=True, stat='density', alpha=0.7, label='Null Distribution')
    plt.axvline(x=observed_val, color='red', linestyle='--', linewidth=2, label=f'Observed ({observed_val:.4f})')
    plt.title(title)
    plt.xlabel('Statistic Value')
    plt.ylabel('Density')
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Histogram saved to {output_path}")

def plot_primary_threshold_visualizations(results: List[Dict[str, Any]], datasets: Dict[str, pd.DataFrame], output_dir: str) -> None:
    """
    Generate primary threshold visualizations for |r| > 0.3.
    This includes heatmap and histogram for the primary threshold.
    """
    # Assuming results contain the necessary data for plotting
    # We'll generate a heatmap of the correlation matrix and a histogram of the null distribution
    
    # For simplicity, we use the first dataset's results
    if not results:
        print("No results provided for primary threshold visualization.")
        return
    
    res = results[0]
    ds_id = list(datasets.keys())[0]
    df = datasets[ds_id]
    
    # Plot heatmap
    corr_matrix = df.corr(method='pearson').abs()
    plot_heatmap(corr_matrix, f"Correlation Matrix (|r| > 0.3) for {ds_id}", os.path.join(output_dir, f"heatmap_{ds_id}_primary.png"))
    
    # Plot histogram for each statistic
    for stat_name, null_dist in res['null_dist'].items():
        observed_val = res['observed'][stat_name]
        plot_histogram(
            null_dist, 
            observed_val, 
            f"Null Distribution for {stat_name} ({ds_id})", 
            os.path.join(output_dir, f"histogram_{ds_id}_{stat_name}_primary.png")
        )

def plot_sensitivity_sweep(df_sens: pd.DataFrame, output_path: str) -> None:
    """
    Generate a plot showing the variation in significant counts across thresholds.
    """
    plt.figure(figsize=(10, 6))
    sns.lineplot(data=df_sens, x='threshold', y='count', marker='o')
    plt.title('Sensitivity Analysis: Significant Counts vs Threshold')
    plt.xlabel('Correlation Threshold |r|')
    plt.ylabel('Number of Significant Associations')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Sensitivity sweep plot saved to {output_path}")

def plot_observed_vs_null_heatmap(observed_matrix: pd.DataFrame, null_dist: Dict[str, List[float]], output_path: str) -> None:
    """
    Generate a heatmap comparing observed correlations to null expectations.
    This is a simplified version; in practice, you'd compute the mean of the null distribution for each edge.
    """
    # Create a matrix of mean null values
    null_matrix = pd.DataFrame(0.0, index=observed_matrix.index, columns=observed_matrix.columns)
    
    # This is a placeholder; in reality, you'd need to map the null distribution back to the matrix structure
    # For now, we just plot the observed matrix as a reference
    plot_heatmap(observed_matrix, "Observed vs Null (Simplified)", output_path)
