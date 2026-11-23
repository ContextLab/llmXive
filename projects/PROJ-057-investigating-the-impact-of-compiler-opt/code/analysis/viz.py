"""
Visualization module for compiler optimization impact analysis.
Generates Pareto frontier plots and error distribution visualizations.
"""
import os
import logging
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
STABILITY_THRESHOLD = 1e-5
DATA_DIR = Path("data")
RESULTS_DIR = DATA_DIR / "results"
INTERMEDIATES_DIR = DATA_DIR / "intermediates"

def load_stability_metrics() -> pd.DataFrame:
    """
    Load stability metrics from the aggregated CSV.
    Returns:
        DataFrame with stability metrics.
    """
    metrics_path = RESULTS_DIR / "stability_metrics.csv"
    if not metrics_path.exists():
        raise FileNotFoundError(f"Stability metrics file not found: {metrics_path}")
    
    df = pd.read_csv(metrics_path)
    logger.info(f"Loaded {len(df)} stability metrics from {metrics_path}")
    return df

def parse_optimization_level(config_id: str) -> Tuple[str, str]:
    """
    Parse optimization level and compiler from config_id.
    Expected format: 'compiler_level' (e.g., 'gcc_O2', 'clang_O3')
    
    Args:
        config_id: Configuration identifier string.
    
    Returns:
        Tuple of (compiler, level).
    """
    parts = config_id.split('_')
    if len(parts) >= 2:
        return parts[0], parts[1]
    return "unknown", config_id

def plot_pareto_frontier(
    df: pd.DataFrame,
    x_col: str = "median_ms",
    y_col: str = "max_diff",
    title: str = "Pareto Frontier",
    output_path: Optional[Path] = None,
    exclude_unstable: bool = False,
    highlight_downsampled: bool = False
) -> plt.Figure:
    """
    Generate a Pareto frontier plot of latency vs error.
    
    Args:
        df: DataFrame containing configuration data.
        x_col: Column name for x-axis (latency).
        y_col: Column name for y-axis (error).
        title: Plot title.
        output_path: Path to save the figure.
        exclude_unstable: If True, exclude rows with status='unstable'.
        highlight_downsampled: If True, highlight downsampled configurations.
    
    Returns:
        Matplotlib figure object.
    """
    plot_df = df.copy()
    
    if exclude_unstable:
        stable_df = plot_df[plot_df.get("status", "stable") == "stable"]
        logger.info(f"Filtered to {len(stable_df)} stable configurations for final plot")
        plot_df = stable_df
    
    if plot_df.empty:
        logger.warning("No data points to plot after filtering.")
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.text(0.5, 0.5, "No valid data to plot", transform=ax.transAxes, ha='center')
        plt.close(fig)
        return fig

    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Identify downsampled points if requested
    if highlight_downsampled and "downsampled" in plot_df.columns:
        downsampled_mask = plot_df["downsampled"] == True
        stable_mask = ~downsampled_mask
    else:
        downsampled_mask = pd.Series([False] * len(plot_df), index=plot_df.index)
        stable_mask = pd.Series([True] * len(plot_df), index=plot_df.index)

    # Plot non-downsampled points
    if stable_mask.any():
        ax.scatter(
            plot_df.loc[stable_mask, x_col],
            plot_df.loc[stable_mask, y_col],
            alpha=0.6,
            label='Stable',
            edgecolors='black',
            s=50
        )
    
    # Plot downsampled points with distinct marker
    if highlight_downsampled and downsampled_mask.any():
        ax.scatter(
            plot_df.loc[downsampled_mask, x_col],
            plot_df.loc[downsampled_mask, y_col],
            alpha=0.8,
            label='Downsampled',
            marker='X',
            s=100,
            edgecolors='red',
            linewidths=1.5
        )
    
    # Calculate and plot Pareto frontier
    pareto_points = []
    sorted_df = plot_df.sort_values(by=[x_col, y_col])
    
    min_y = float('inf')
    for _, row in sorted_df.iterrows():
        if row[y_col] <= min_y:
            pareto_points.append(row)
            min_y = row[y_col]
    
    if pareto_points:
        pareto_df = pd.DataFrame(pareto_points)
        pareto_df = pareto_df.sort_values(by=x_col)
        ax.plot(
            pareto_df[x_col],
            pareto_df[y_col],
            'r-',
            linewidth=2,
            label='Pareto Frontier'
        )
    
    ax.set_xlabel("Median Latency (ms)")
    ax.set_ylabel("Max Absolute Difference")
    ax.set_title(title)
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        logger.info(f"Pareto frontier plot saved to {output_path}")
    
    return fig

def generate_pareto_exploration() -> Path:
    """
    Generate Pareto exploration plot including ALL configurations (stable and unstable).
    Unstable configurations are marked with a warning style (red outline).
    Downsampled configurations are marked with a distinct indicator.
    
    Returns:
        Path to the generated plot file.
    """
    df = load_stability_metrics()
    
    # Mark unstable configurations
    unstable_mask = df.get("status", "stable") == "unstable"
    downsampled_mask = df.get("downsampled", False) == True
    
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Plot stable, non-downsampled
    mask_stable_normal = ~unstable_mask & ~downsampled_mask
    if mask_stable_normal.any():
        ax.scatter(
            df.loc[mask_stable_normal, "median_ms"],
            df.loc[mask_stable_normal, "max_diff"],
            alpha=0.6,
            label='Stable (Normal)',
            edgecolors='black',
            s=60
        )
    
    # Plot stable, downsampled
    mask_stable_down = ~unstable_mask & downsampled_mask
    if mask_stable_down.any():
        ax.scatter(
            df.loc[mask_stable_down, "median_ms"],
            df.loc[mask_stable_down, "max_diff"],
            alpha=0.8,
            label='Stable (Downsampled)',
            marker='X',
            s=100,
            edgecolors='blue',
            linewidths=1.5
        )
    
    # Plot unstable (warning style)
    if unstable_mask.any():
        ax.scatter(
            df.loc[unstable_mask, "median_ms"],
            df.loc[unstable_mask, "max_diff"],
            alpha=0.7,
            label='Unstable (Warning)',
            facecolors='none',
            edgecolors='red',
            linewidths=2,
            s=80
        )
    
    # Calculate Pareto frontier on ALL data
    sorted_df = df.sort_values(by=["median_ms", "max_diff"])
    pareto_points = []
    min_y = float('inf')
    for _, row in sorted_df.iterrows():
        if row["max_diff"] <= min_y:
            pareto_points.append(row)
            min_y = row["max_diff"]
    
    if pareto_points:
        pareto_df = pd.DataFrame(pareto_points)
        pareto_df = pareto_df.sort_values(by="median_ms")
        ax.plot(
            pareto_df["median_ms"],
            pareto_df["max_diff"],
            'g--',
            linewidth=2,
            label='Exploration Frontier'
        )
    
    ax.set_xlabel("Median Latency (ms)")
    ax.set_ylabel("Max Absolute Difference")
    ax.set_title("Pareto Frontier Exploration (All Configurations)")
    ax.legend(loc='upper right')
    ax.grid(True, alpha=0.3)
    
    output_path = RESULTS_DIR / "pareto_frontier_exploration.png"
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    
    logger.info(f"Exploration plot saved to {output_path}")
    return output_path

def generate_pareto_final() -> Tuple[Path, Path]:
    """
    Generate final Pareto frontier plot strictly excluding unstable configurations.
    Also generates aggregated.csv with only stable configurations.
    
    Returns:
        Tuple of (plot_path, csv_path).
    """
    df = load_stability_metrics()
    
    # Filter to stable only
    stable_df = df[df.get("status", "stable") == "stable"]
    
    if stable_df.empty:
        logger.warning("No stable configurations found for final plot.")
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.text(0.5, 0.5, "No stable data to plot", transform=ax.transAxes, ha='center')
        plot_path = RESULTS_DIR / "pareto_frontier_final.png"
        plt.savefig(plot_path, dpi=150)
        plt.close(fig)
        return plot_path, RESULTS_DIR / "aggregated.csv"
    
    # Generate plot
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Plot all stable points
    ax.scatter(
        stable_df["median_ms"],
        stable_df["max_diff"],
        alpha=0.6,
        label='Stable Configurations',
        edgecolors='black',
        s=60
    )
    
    # Calculate Pareto frontier
    sorted_df = stable_df.sort_values(by=["median_ms", "max_diff"])
    pareto_points = []
    min_y = float('inf')
    for _, row in sorted_df.iterrows():
        if row["max_diff"] <= min_y:
            pareto_points.append(row)
            min_y = row["max_diff"]
    
    if pareto_points:
        pareto_df = pd.DataFrame(pareto_points)
        pareto_df = pareto_df.sort_values(by="median_ms")
        ax.plot(
            pareto_df["median_ms"],
            pareto_df["max_diff"],
            'r-',
            linewidth=2,
            label='Pareto Frontier'
        )
    
    ax.set_xlabel("Median Latency (ms)")
    ax.set_ylabel("Max Absolute Difference")
    ax.set_title("Pareto Frontier (Stable Configurations Only)")
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plot_path = RESULTS_DIR / "pareto_frontier_final.png"
    plt.savefig(plot_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    
    # Generate aggregated CSV
    csv_path = RESULTS_DIR / "aggregated.csv"
    stable_df.to_csv(csv_path, index=False)
    
    logger.info(f"Final plot saved to {plot_path}")
    logger.info(f"Aggregated CSV saved to {csv_path} with {len(stable_df)} rows")
    
    return plot_path, csv_path

def main():
    """Main entry point for visualization tasks."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate visualization plots for compiler optimization analysis.")
    parser.add_argument(
        "--plot-exploration",
        action="store_true",
        help="Generate exploration plot including all configurations."
    )
    parser.add_argument(
        "--plot-final",
        action="store_true",
        help="Generate final plot excluding unstable configurations."
    )
    
    args = parser.parse_args()
    
    # Ensure output directory exists
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    
    if args.plot_exploration:
        logger.info("Generating exploration plot...")
        generate_pareto_exploration()
    
    if args.plot_final:
        logger.info("Generating final plot...")
        generate_pareto_final()
    
    if not (args.plot_exploration or args.plot_final):
        parser.print_help()

if __name__ == "__main__":
    main()