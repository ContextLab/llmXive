import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from typing import List, Optional, Dict, Any
import os
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def plot_heatmap(corr_matrix: pd.DataFrame, output_path: str):
    """Plot a correlation heatmap."""
    plt.figure(figsize=(10, 8))
    sns.heatmap(corr_matrix, annot=False, cmap='coolwarm', center=0)
    plt.title('Correlation Matrix Heatmap')
    plt.tight_layout()
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path)
    plt.close()
    logger.info(f"Heatmap saved to {output_path}")

def plot_histogram(data: np.ndarray, output_path: str):
    """Plot a histogram of data."""
    plt.figure(figsize=(8, 6))
    plt.hist(data, bins=30, edgecolor='black', alpha=0.7)
    plt.title('Distribution of Null Statistics')
    plt.xlabel('Value')
    plt.ylabel('Frequency')
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path)
    plt.close()
    logger.info(f"Histogram saved to {output_path}")

def plot_primary_threshold_visualizations(
    corr_matrix: pd.DataFrame, 
    null_dist: np.ndarray, 
    output_prefix: str
):
    """Plot primary threshold visualizations."""
    plot_heatmap(corr_matrix, f"{output_prefix}_heatmap.png")
    plot_histogram(null_dist, f"{output_prefix}_hist.png")

def main():
    """Main entry point for viz module (for testing)."""
    pass

if __name__ == "__main__":
    pass