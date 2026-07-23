import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from typing import List, Optional, Dict, Any
import os

def plot_heatmap(corr_matrix: pd.DataFrame, output_path: str):
    """Plot correlation heatmap."""
    plt.figure(figsize=(10, 8))
    sns.heatmap(corr_matrix, annot=False, cmap='coolwarm', center=0)
    plt.title('Correlation Heatmap')
    plt.tight_layout()
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path)
    plt.close()

def plot_histogram(data: List[float], output_path: str, title: str = 'Histogram'):
    """Plot histogram."""
    plt.figure(figsize=(8, 6))
    plt.hist(data, bins=30, edgecolor='black')
    plt.title(title)
    plt.xlabel('Value')
    plt.ylabel('Frequency')
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path)
    plt.close()

def plot_primary_threshold_visualizations(results_df: pd.DataFrame, output_dir: str):
    """Plot primary threshold visualizations."""
    os.makedirs(output_dir, exist_ok=True)
    # Example: plot density vs threshold
    if 'threshold' in results_df.columns and 'density' in results_df.columns:
        plt.figure(figsize=(8, 6))
        for ds_name in results_df['dataset_name'].unique():
            subset = results_df[results_df['dataset_name'] == ds_name]
            plt.plot(subset['threshold'], subset['density'], marker='o', label=ds_name)
        plt.xlabel('Threshold')
        plt.ylabel('Density')
        plt.title('Threshold Sensitivity: Density')
        plt.legend()
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'threshold_sensitivity_density.png'))
        plt.close()

def main():
    # Example usage
    df = pd.DataFrame(np.random.rand(10, 10), columns=[f'var_{i}' for i in range(10)])
    corr = df.corr()
    plot_heatmap(corr, 'output/plots/test_heatmap.png')
    print("Plot saved.")
