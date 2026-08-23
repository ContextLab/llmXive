import os
import sys
import logging
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

from config import get_config
from utils.logging_config import log_info_with_context, log_error_with_context

logger = logging.getLogger(__name__)
sns.set(style="whitegrid")

def load_data(encoded_path: str, frontier_path: str, cluster_path: str):
    """Loads all necessary data for visualization."""
    encoded_df = pd.read_csv(encoded_path)
    frontier_df = pd.read_csv(frontier_path)
    cluster_df = pd.read_csv(cluster_path) if os.path.exists(cluster_path) else None
    return encoded_df, frontier_df, cluster_df

def plot_trade_off_space(encoded_df: pd.DataFrame, frontier_df: pd.DataFrame, cluster_df: pd.DataFrame, output_path: str):
    """Generates a 2D plot showing compositional space, decoupled regions, and Pareto frontier."""
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Plot empirical data
    ax.scatter(
        encoded_df["bulk_modulus"],
        encoded_df["shear_modulus"],
        alpha=0.5,
        label="Empirical Data",
        color="gray"
    )
    
    # Plot Pareto frontier
    if not frontier_df.empty:
        ax.scatter(
            frontier_df.iloc[:, 0],
            frontier_df.iloc[:, 1],
            color="red",
            label="Pareto Frontier",
            edgecolors="black"
        )
    
    # Highlight decoupled region if available
    if cluster_df is not None and "cluster" in cluster_df.columns:
        # Assume cluster 0 is the decoupled region (placeholder logic)
        decoupled = cluster_df[cluster_df["cluster"] == 0]
        if not decoupled.empty:
            ax.scatter(
                decoupled["bulk_modulus"],
                decoupled["shear_modulus"],
                color="blue",
                label="Decoupled Region",
                marker="x",
                s=100
            )
    
    ax.set_xlabel("Bulk Modulus")
    ax.set_ylabel("Shear Modulus")
    ax.set_title("Multi-Property Trade-Off Space")
    ax.legend()
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    log_info_with_context(f"Saved visualization to {output_path}", context="visualization")

def main():
    """Main entry point for visualization."""
    config = get_config()
    processed_dir = config.get("processed_dir", "data/processed")
    results_dir = config.get("results_dir", "data/results")
    
    encoded_path = os.path.join(processed_dir, "encoded_alloys.csv")
    frontier_path = os.path.join(processed_dir, "pareto_frontier.csv")
    cluster_path = os.path.join(processed_dir, "clustering_results.csv")
    output_path = os.path.join(results_dir, "decoupling_plot.png")
    
    try:
        encoded_df, frontier_df, cluster_df = load_data(encoded_path, frontier_path, cluster_path)
        
        os.makedirs(results_dir, exist_ok=True)
        plot_trade_off_space(encoded_df, frontier_df, cluster_df, output_path)
        
        log_info_with_context("Visualization completed successfully", context="visualization")
        return 0
    except Exception as e:
        log_error_with_context(f"Visualization failed: {str(e)}", context="visualization")
        return 1

if __name__ == "__main__":
    sys.exit(main())
