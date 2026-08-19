import os
import sys
import json
import argparse
import logging
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Ensure consistent styling
sns.set(style="whitegrid", context="talk")
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans', 'Lucida Grande']

from config import get_processed_data_path, get_figures_path, ensure_dirs
from utils.logging import get_experiment_logger

logger = get_experiment_logger(__name__)

# Density mapping based on T025/T028 requirements: {1, 3, 5, 10}
# Mapped to low, medium, high categories for visualization
DENSITY_MAPPING = {
    1: "Low",
    3: "Medium",
    5: "High",
    10: "High" # Grouping 10 with High for clearer comparison, or keep separate if needed
}

# Explicitly define the order for plotting
DENSITY_ORDER = ["Low", "Medium", "High"]

def load_metrics_data(metrics_path: str) -> pd.DataFrame:
    """
    Loads the aggregated metrics report from the simulation run.
    Expects a JSON or CSV file containing alignment scores and density levels.
    """
    path = Path(metrics_path)
    if not path.exists():
        raise FileNotFoundError(f"Metrics file not found at {metrics_path}. "
                                "Please run the simulation and aggregation steps first.")
    
    if path.suffix == '.csv':
        df = pd.read_csv(path)
    elif path.suffix == '.json':
        with open(path, 'r') as f:
            data = json.load(f)
        df = pd.DataFrame(data)
    else:
        # Try CSV as default
        df = pd.read_csv(path)
    
    # Ensure required columns exist
    required_cols = ['density_level', 'alignment_score', 'latency_ms']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Metrics file missing required columns: {missing}")
    
    return df

def calculate_pareto_frontier(df: pd.DataFrame) -> pd.DataFrame:
    """
    Identifies the Pareto frontier points from the dataframe.
    A point is Pareto optimal if no other point has both better (lower) latency 
    and better (higher) alignment score.
    """
    # Sort by latency (ascending) then alignment (descending)
    # We want to maximize alignment and minimize latency.
    df_sorted = df.sort_values(by=['latency_ms', 'alignment_score'], ascending=[True, False])
    
    frontier = []
    max_alignment_so_far = -np.inf
    
    # Iterate through sorted data
    # Since we sorted by latency ascending, as we go, latency increases (or stays same).
    # We want to find points where alignment is higher than any previous point (with lower latency).
    # Actually, standard Pareto: Point A dominates B if A.latency <= B.latency AND A.alignment >= B.alignment, with at least one strict inequality.
    # We want the set of non-dominated points.
    
    # Let's do a simple O(N^2) check for correctness or a sweep line.
    # Sweep line: Sort by latency ascending. Keep track of max alignment seen so far.
    # If current point has alignment > max_alignment_so_far, it is on the frontier (because it has higher alignment than any point with lower/equal latency).
    
    for _, row in df_sorted.iterrows():
        if row['alignment_score'] > max_alignment_so_far:
            frontier.append(row)
            max_alignment_so_far = row['alignment_score']
    
    return pd.DataFrame(frontier)

def plot_pareto_frontier(df: pd.DataFrame, output_path: str):
    """
    Generates the Pareto frontier plot (Alignment vs. Latency).
    """
    frontier_df = calculate_pareto_frontier(df)
    
    plt.figure(figsize=(10, 7))
    
    # Plot all points
    plt.scatter(df['latency_ms'], df['alignment_score'], 
                alpha=0.3, color='gray', label='All Simulations')
    
    # Plot frontier
    if not frontier_df.empty:
        plt.plot(frontier_df['latency_ms'], frontier_df['alignment_score'], 
                 'r-o', linewidth=2, markersize=8, label='Pareto Frontier')
    
    plt.xlabel('Latency (ms)', fontsize=12)
    plt.ylabel('Alignment Score', fontsize=12)
    plt.title('Pareto Frontier: Alignment vs. Latency', fontsize=14)
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Save
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    logger.info(f"Pareto frontier plot saved to {output_path}")

def plot_alignment_by_density(df: pd.DataFrame, output_path: str):
    """
    Plots alignment scores across information density levels (low, medium, high).
    This addresses T036: visualizing the impact of density on alignment.
    """
    # Map density levels to categories
    df['density_category'] = df['density_level'].map(DENSITY_MAPPING)
    
    # Ensure all categories are present in the order we want, even if some data is missing
    df['density_category'] = pd.Categorical(
        df['density_category'], 
        categories=DENSITY_ORDER, 
        ordered=True
    )
    
    # Drop rows where mapping failed (if any unexpected density levels exist)
    df_plot = df.dropna(subset=['density_category'])
    
    if df_plot.empty:
        logger.warning("No valid data to plot for density analysis.")
        # Create an empty plot to avoid crashing
        plt.figure(figsize=(10, 7))
        plt.text(0.5, 0.5, 'No Data Available', ha='center', va='center', transform=plt.gca().transAxes)
        plt.title('Alignment Scores by Information Density (No Data)')
        plt.savefig(output_path, dpi=300)
        plt.close()
        return

    plt.figure(figsize=(10, 7))
    
    # Use boxplot to show distribution and outliers
    # Or barplot with error bars for mean/CI
    # Boxplot is better for seeing distribution spread
    sns.boxplot(data=df_plot, x='density_category', y='alignment_score', 
                palette="viridis", order=DENSITY_ORDER)
    
    # Add swarmplot for individual points
    sns.swarmplot(data=df_plot, x='density_category', y='alignment_score', 
                  color="black", size=4, alpha=0.6, order=DENSITY_ORDER)
    
    plt.xlabel('Information Density', fontsize=12)
    plt.ylabel('Alignment Score', fontsize=12)
    plt.title('Alignment Scores Across Information Density Levels', fontsize=14)
    plt.grid(axis='y', alpha=0.3)
    
    # Save
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    logger.info(f"Alignment by density plot saved to {output_path}")

def main():
    """
    CLI entry point for generating visualization reports.
    """
    parser = argparse.ArgumentParser(description="Generate analysis visualizations")
    parser.add_argument('--metrics-path', type=str, default=None,
                        help="Path to the aggregated metrics file (CSV/JSON). "
                             "If not provided, uses default path from config.")
    parser.add_argument('--output-dir', type=str, default=None,
                        help="Directory to save figures. Defaults to config figures path.")
    parser.add_argument('--plot-type', type=str, choices=['pareto', 'density', 'all'], default='all',
                        help="Which plots to generate.")
    
    args = parser.parse_args()
    
    # Resolve paths
    metrics_path = args.metrics_path or str(get_processed_data_path() / "metrics_report.csv")
    output_dir = Path(args.output_dir) if args.output_dir else get_figures_path()
    ensure_dirs(output_dir)
    
    try:
        df = load_metrics_data(metrics_path)
        logger.info(f"Loaded {len(df)} records from {metrics_path}")
    except Exception as e:
        logger.error(f"Failed to load metrics data: {e}")
        sys.exit(1)
    
    if args.plot_type in ['pareto', 'all']:
        pareto_path = output_dir / "pareto_frontier.png"
        plot_pareto_frontier(df, str(pareto_path))
    
    if args.plot_type in ['density', 'all']:
        density_path = output_dir / "alignment_by_density.png"
        plot_alignment_by_density(df, str(density_path))
    
    logger.info("Visualization generation complete.")

if __name__ == "__main__":
    main()