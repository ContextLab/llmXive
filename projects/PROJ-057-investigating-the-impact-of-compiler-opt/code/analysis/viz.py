"""
Visualization module for Pareto Frontier analysis.
Generates exploration and final plots for compiler optimization configurations.
"""

import os
import logging
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_stability_metrics(csv_path: str) -> pd.DataFrame:
    """
    Load stability metrics from CSV file.
    
    Args:
        csv_path: Path to stability_metrics.csv
        
    Returns:
        DataFrame with stability metrics
    """
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"Stability metrics file not found: {csv_path}")
    
    df = pd.read_csv(csv_path)
    logger.info(f"Loaded {len(df)} rows from {csv_path}")
    return df

def parse_optimization_level(config_id: str) -> str:
    """
    Extract optimization level from config_id.
    
    Args:
        config_id: Configuration identifier string
        
    Returns:
        Optimization level string (e.g., 'O0', 'O2', 'O3')
    """
    # Expected format: kernel_optlevel_dim_downsampled or similar
    parts = config_id.split('_')
    for part in parts:
        if part.startswith('O') and len(part) == 2 and part[1].isdigit():
            return part
    return 'unknown'

def plot_pareto_frontier(
    df: pd.DataFrame,
    x_col: str = 'median_latency',
    y_col: str = 'max_abs_diff',
    title: str = 'Pareto Frontier',
    x_label: str = 'Median Latency (ms)',
    y_label: str = 'Max Absolute Difference',
    output_path: Optional[str] = None,
    exclude_threshold: float = 1e-5,
    show_downsampled: bool = True,
    downsampled_marker: str = 'X',
    downsampled_color: str = 'red',
    stable_marker: str = 'o',
    stable_color: str = 'blue'
) -> plt.Figure:
    """
    Plot Pareto frontier for stable configurations.
    
    Args:
        df: DataFrame with latency and error metrics
        x_col: Column name for x-axis (latency)
        y_col: Column name for y-axis (error)
        title: Plot title
        x_label: X-axis label
        y_label: Y-axis label
        output_path: Path to save the figure
        exclude_threshold: Error threshold for exclusion
        show_downsampled: Whether to show downsampled configurations
        downsampled_marker: Marker style for downsampled configs
        downsampled_color: Color for downsampled configs
        stable_marker: Marker style for stable configs
        stable_color: Color for stable configs
        
    Returns:
        Matplotlib Figure object
    """
    # Filter for stable configurations (error <= threshold)
    stable_df = df[df[y_col] <= exclude_threshold].copy()
    
    if stable_df.empty:
        logger.warning("No stable configurations found for plotting")
        fig, ax = plt.subplots(figsize=(10, 8))
        ax.text(0.5, 0.5, 'No stable configurations found', 
               transform=ax.transAxes, ha='center', va='center', fontsize=14)
        ax.set_xlabel(x_label)
        ax.set_ylabel(y_label)
        ax.set_title(title)
        return fig
    
    # Separate downsampled and standard runs
    downsampled_mask = stable_df['config_id'].str.contains('downsampled', case=False, na=False)
    standard_df = stable_df[~downsampled_mask]
    downsampled_df = stable_df[downsampled_mask]
    
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Plot standard configurations
    if not standard_df.empty:
        ax.scatter(
            standard_df[x_col],
            standard_df[y_col],
            marker=stable_marker,
            c=stable_color,
            alpha=0.7,
            label='Standard Runs',
            s=100,
            edgecolors='black',
            linewidths=0.5
        )
        
        # Add labels for standard runs
        for idx, row in standard_df.iterrows():
            ax.annotate(
                row['config_id'],
                (row[x_col], row[y_col]),
                xytext=(5, 5),
                textcoords='offset points',
                fontsize=8,
                alpha=0.7
            )
    
    # Plot downsampled configurations with distinct marker
    if show_downsampled and not downsampled_df.empty:
        ax.scatter(
            downsampled_df[x_col],
            downsampled_df[y_col],
            marker=downsampled_marker,
            c=downsampled_color,
            alpha=0.8,
            label='Downsampled Runs',
            s=150,
            edgecolors='black',
            linewidths=0.5
        )
        
        # Add labels for downsampled runs
        for idx, row in downsampled_df.iterrows():
            ax.annotate(
                row['config_id'],
                (row[x_col], row[y_col]),
                xytext=(5, -10),
                textcoords='offset points',
                fontsize=8,
                alpha=0.7,
                color=downsampled_color
            )
    
    # Calculate and plot Pareto frontier
    # Sort by x-axis (latency) ascending
    sorted_df = stable_df.sort_values(by=x_col)
    
    # Find Pareto frontier: points where no other point is better in both metrics
    pareto_points = []
    for idx, row in sorted_df.iterrows():
        is_pareto = True
        for other_idx, other_row in sorted_df.iterrows():
            if other_row[x_col] <= row[x_col] and other_row[y_col] <= row[y_col]:
                if other_row[x_col] < row[x_col] or other_row[y_col] < row[y_col]:
                    is_pareto = False
                    break
        if is_pareto:
            pareto_points.append((row[x_col], row[y_col]))
    
    if pareto_points:
        pareto_x = [p[0] for p in pareto_points]
        pareto_y = [p[1] for p in pareto_points]
        ax.plot(pareto_x, pareto_y, 'g--', linewidth=2, label='Pareto Frontier', alpha=0.8)
    
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.set_title(title)
    ax.legend(loc='upper right')
    ax.grid(True, alpha=0.3)
    ax.set_xlim(left=0)
    ax.set_ylim(bottom=0)
    
    plt.tight_layout()
    
    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        logger.info(f"Pareto frontier plot saved to {output_path}")
    
    return fig

def generate_pareto_exploration(
    stability_metrics_path: str,
    output_path: str,
    exclude_threshold: float = 1e-5
) -> None:
    """
    Generate Pareto frontier exploration plot including all stable configurations.
    
    This function creates a plot that includes:
    - All numerically stable configurations (error <= threshold)
    - Both standard and downsampled runs
    - Distinct visual markers for downsampled configurations
    - Pareto frontier line connecting optimal points
    
    Args:
        stability_metrics_path: Path to stability_metrics.csv
        output_path: Path to save the exploration plot
        exclude_threshold: Error threshold for stability (default 1e-5)
    """
    logger.info(f"Generating Pareto exploration plot from {stability_metrics_path}")
    
    # Load stability metrics
    df = load_stability_metrics(stability_metrics_path)
    
    # Ensure required columns exist
    required_cols = ['config_id', 'median_latency', 'max_abs_diff']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    # Generate the exploration plot
    fig = plot_pareto_frontier(
        df=df,
        x_col='median_latency',
        y_col='max_abs_diff',
        title='Pareto Frontier Exploration (All Stable Configurations)',
        x_label='Median Latency (ms)',
        y_label='Max Absolute Difference',
        output_path=output_path,
        exclude_threshold=exclude_threshold,
        show_downsampled=True,
        downsampled_marker='X',
        downsampled_color='red',
        stable_marker='o',
        stable_color='blue'
    )
    
    plt.close(fig)
    logger.info(f"Exploration plot generated: {output_path}")

def generate_pareto_final(
    stability_metrics_path: str,
    output_path: str,
    exclude_threshold: float = 1e-5
) -> None:
    """
    Generate final Pareto frontier plot excluding unstable configurations.
    
    This function creates a strict Pareto frontier plot that:
    - Excludes all configurations with error > threshold
    - Only includes numerically stable runs
    - Does not distinguish downsampled runs (all treated equally)
    
    Args:
        stability_metrics_path: Path to stability_metrics.csv
        output_path: Path to save the final plot
        exclude_threshold: Error threshold for stability (default 1e-5)
    """
    logger.info(f"Generating Pareto final plot from {stability_metrics_path}")
    
    # Load stability metrics
    df = load_stability_metrics(stability_metrics_path)
    
    # Ensure required columns exist
    required_cols = ['config_id', 'median_latency', 'max_abs_diff']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    # Generate the final plot (no special downsampled marking)
    fig = plot_pareto_frontier(
        df=df,
        x_col='median_latency',
        y_col='max_abs_diff',
        title='Final Pareto Frontier (Stable Configurations Only)',
        x_label='Median Latency (ms)',
        y_label='Max Absolute Difference',
        output_path=output_path,
        exclude_threshold=exclude_threshold,
        show_downsampled=False,  # Treat all stable runs equally
        stable_marker='o',
        stable_color='blue'
    )
    
    plt.close(fig)
    logger.info(f"Final Pareto plot generated: {output_path}")

def main():
    """Main entry point for visualization generation."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate Pareto frontier plots')
    parser.add_argument(
        '--stability-metrics',
        type=str,
        default='data/results/stability_metrics.csv',
        help='Path to stability metrics CSV file'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='data/results',
        help='Output directory for plots'
    )
    parser.add_argument(
        '--threshold',
        type=float,
        default=1e-5,
        help='Error threshold for stability (default: 1e-5)'
    )
    
    args = parser.parse_args()
    
    # Ensure output directory exists
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate exploration plot
    exploration_path = output_dir / 'pareto_frontier_exploration.png'
    generate_pareto_exploration(
        stability_metrics_path=args.stability_metrics,
        output_path=str(exploration_path),
        exclude_threshold=args.threshold
    )
    
    # Generate final plot
    final_path = output_dir / 'pareto_frontier_final.png'
    generate_pareto_final(
        stability_metrics_path=args.stability_metrics,
        output_path=str(final_path),
        exclude_threshold=args.threshold
    )
    
    print(f"Generated plots:")
    print(f"  - {exploration_path}")
    print(f"  - {final_path}")

if __name__ == '__main__':
    main()
