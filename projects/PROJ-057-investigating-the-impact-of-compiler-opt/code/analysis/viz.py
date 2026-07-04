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
    Load stability metrics from a CSV file.
    
    Args:
        csv_path: Path to the stability metrics CSV file.
        
    Returns:
        DataFrame containing stability metrics.
    """
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"Stability metrics file not found: {csv_path}")
    
    logger.info(f"Loading stability metrics from {csv_path}")
    df = pd.read_csv(path)
    
    required_cols = ['config_id', 'kernel_type', 'l2_error', 'max_diff', 'status']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in {csv_path}: {missing}")
    
    return df

def parse_optimization_level(config_id: str) -> str:
    """
    Extract optimization level from config_id.
    
    Args:
        config_id: Configuration identifier string.
        
    Returns:
        Optimization level string (e.g., 'O0', 'O2', 'O3', 'fast-math').
    """
    # Handle various config_id formats
    if 'O0' in config_id:
        return 'O0'
    elif 'O1' in config_id:
        return 'O1'
    elif 'O2' in config_id:
        return 'O2'
    elif 'O3' in config_id:
        return 'O3'
    elif 'Os' in config_id:
        return 'Os'
    elif 'ffast-math' in config_id:
        return 'fast-math'
    elif 'funroll-loops' in config_id:
        return 'unroll'
    else:
        # Default to the full config_id if no standard flag found
        return config_id

def plot_pareto_frontier(
    df: pd.DataFrame,
    x_col: str = 'median_latency',
    y_col: str = 'max_abs_diff',
    title: str = 'Pareto Frontier',
    output_path: Optional[str] = None,
    stable_only: bool = True,
    error_threshold: float = 1e-5,
    downsampled_marker: str = 's',
    standard_marker: str = 'o',
    downsampled_color: str = 'orange',
    standard_color: str = 'blue'
) -> None:
    """
    Plot Pareto frontier of latency vs. error.
    
    Args:
        df: DataFrame containing latency and error data.
        x_col: Column name for latency (x-axis).
        y_col: Column name for error (y-axis).
        title: Plot title.
        output_path: Path to save the plot (if None, show instead).
        stable_only: If True, filter out unstable configurations.
        error_threshold: Threshold for stability (error <= threshold is stable).
        downsampled_marker: Marker style for downsampled configs.
        standard_marker: Marker style for standard configs.
        downsampled_color: Color for downsampled configs.
        standard_color: Color for standard configs.
    """
    logger.info(f"Plotting Pareto frontier: {x_col} vs {y_col}")
    
    # Filter data
    plot_df = df.copy()
    if stable_only:
        plot_df = plot_df[plot_df['status'] == 'stable']
        logger.info(f"Filtered to stable configs only (error <= {error_threshold})")
    
    if plot_df.empty:
        logger.warning("No data points available for plotting after filtering.")
        return
    
    # Identify downsampled configurations (assuming config_id contains 'downsampled' or similar)
    # Adjust this logic based on actual config_id format
    plot_df['is_downsampled'] = plot_df['config_id'].str.contains('downsampled', case=False, na=False)
    
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Plot standard configurations
    standard_mask = ~plot_df['is_downsampled']
    if standard_mask.any():
        ax.scatter(
            plot_df.loc[standard_mask, x_col],
            plot_df.loc[standard_mask, y_col],
            marker=standard_marker,
            color=standard_color,
            alpha=0.6,
            label='Standard',
            s=100
        )
    
    # Plot downsampled configurations
    downsampled_mask = plot_df['is_downsampled']
    if downsampled_mask.any():
        ax.scatter(
            plot_df.loc[downsampled_mask, x_col],
            plot_df.loc[downsampled_mask, y_col],
            marker=downsampled_marker,
            color=downsampled_color,
            alpha=0.6,
            label='Downsampled',
            s=100,
            edgecolors='black',
            linewidths=1.5
        )
    
    # Calculate and plot Pareto frontier
    # Sort by x (latency) ascending
    sorted_df = plot_df.sort_values(by=x_col)
    pareto_x = []
    pareto_y = []
    min_y = float('inf')
    
    for _, row in sorted_df.iterrows():
        if row[y_col] < min_y:
            min_y = row[y_col]
            pareto_x.append(row[x_col])
            pareto_y.append(row[y_col])
    
    if pareto_x:
        ax.plot(pareto_x, pareto_y, 'g-', linewidth=2, label='Pareto Frontier', alpha=0.8)
        # Mark Pareto points
        ax.scatter(pareto_x, pareto_y, color='green', marker='*', s=150, zorder=5, label='Pareto Points')
    
    ax.set_xlabel('Median Latency (ms)')
    ax.set_ylabel('Max Absolute Difference')
    ax.set_title(title)
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Invert y-axis if needed (lower error is better) - optional, depending on preference
    # ax.invert_yaxis()
    
    if output_path:
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        logger.info(f"Pareto frontier plot saved to {output_path}")
    else:
        plt.show()
    
    plt.close(fig)

def generate_pareto_exploration(
    metrics_path: str,
    latency_path: str,
    output_path: str
) -> None:
    """
    Generate Pareto exploration plot including downsampled configurations.
    
    Args:
        metrics_path: Path to stability metrics CSV.
        latency_path: Path to aggregated latency CSV.
        output_path: Path to save the output plot.
    """
    logger.info("Generating Pareto exploration plot...")
    
    # Load data
    stability_df = load_stability_metrics(metrics_path)
    latency_df = pd.read_csv(latency_path)
    
    # Merge data
    merged_df = pd.merge(
        stability_df,
        latency_df,
        on='config_id',
        how='inner'
    )
    
    # For exploration, we include all numerically stable configurations
    # (stable AND downsampled, but EXCLUDING unstable ones with error > 1e-5)
    # The stability_check should have already marked unstable ones
    
    plot_pareto_frontier(
        df=merged_df,
        x_col='median',
        y_col='max_diff',
        title='Pareto Frontier Exploration (All Stable Configs)',
        output_path=output_path,
        stable_only=True,
        error_threshold=1e-5,
        downsampled_marker='s',
        standard_marker='o',
        downsampled_color='orange',
        standard_color='blue'
    )

def generate_pareto_final(
    metrics_path: str,
    latency_path: str,
    output_path: str
) -> None:
    """
    Generate final Pareto frontier plot strictly excluding configurations with error > 1e-5.
    
    This represents the final, validated Pareto frontier (Constitution Principle VI).
    
    Args:
        metrics_path: Path to stability metrics CSV.
        latency_path: Path to aggregated latency CSV.
        output_path: Path to save the output plot.
    """
    logger.info("Generating final Pareto frontier plot...")
    
    # Load data
    stability_df = load_stability_metrics(metrics_path)
    latency_df = pd.read_csv(latency_path)
    
    # Merge data
    merged_df = pd.merge(
        stability_df,
        latency_df,
        on='config_id',
        how='inner'
    )
    
    # STRICTLY exclude configurations with error > 1e-5
    # Constitution Principle VI: Configurations with error > 1e-5 are excluded from final results
    valid_df = merged_df[merged_df['max_diff'] <= 1e-5]
    
    if valid_df.empty:
        logger.error("No valid configurations found for final Pareto frontier (all error > 1e-5).")
        # Create an empty plot with a message
        fig, ax = plt.subplots(figsize=(10, 8))
        ax.text(0.5, 0.5, 'No Valid Configurations\n(Error > 1e-5 for all)', 
                transform=ax.transData, ha='center', va='center', fontsize=14)
        ax.set_xlabel('Median Latency (ms)')
        ax.set_ylabel('Max Absolute Difference')
        ax.set_title('Final Pareto Frontier (No Valid Data)')
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close(fig)
        return
    
    # Identify downsampled configurations for distinct marking
    valid_df['is_downsampled'] = valid_df['config_id'].str.contains('downsampled', case=False, na=False)
    
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Plot standard configurations
    standard_mask = ~valid_df['is_downsampled']
    if standard_mask.any():
        ax.scatter(
            valid_df.loc[standard_mask, 'median'],
            valid_df.loc[standard_mask, 'max_diff'],
            marker='o',
            color='blue',
            alpha=0.7,
            label='Standard',
            s=100
        )
    
    # Plot downsampled configurations with distinct marker
    downsampled_mask = valid_df['is_downsampled']
    if downsampled_mask.any():
        ax.scatter(
            valid_df.loc[downsampled_mask, 'median'],
            valid_df.loc[downsampled_mask, 'max_diff'],
            marker='s',
            color='orange',
            alpha=0.7,
            label='Downsampled',
            s=100,
            edgecolors='black',
            linewidths=1.5
        )
    
    # Calculate Pareto frontier (minimize both latency and error)
    # Sort by latency ascending
    sorted_df = valid_df.sort_values(by='median')
    pareto_x = []
    pareto_y = []
    min_y = float('inf')
    
    for _, row in sorted_df.iterrows():
        if row['max_diff'] < min_y:
            min_y = row['max_diff']
            pareto_x.append(row['median'])
            pareto_y.append(row['max_diff'])
    
    if pareto_x:
        ax.plot(pareto_x, pareto_y, 'g-', linewidth=2, label='Pareto Frontier', alpha=0.8)
        # Mark Pareto points
        ax.scatter(pareto_x, pareto_y, color='green', marker='*', s=150, zorder=5, label='Pareto Points')
    
    ax.set_xlabel('Median Latency (ms)')
    ax.set_ylabel('Max Absolute Difference')
    ax.set_title('Final Pareto Frontier (Stable Configurations Only, Error ≤ 1e-5)')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    logger.info(f"Final Pareto frontier plot saved to {output_path}")
    plt.close(fig)

def main():
    """
    Main entry point for generating Pareto frontier plots.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate Pareto frontier plots')
    parser.add_argument('--mode', choices=['exploration', 'final'], default='final',
                      help='Plot mode: exploration (includes downsampled) or final (strictly stable)')
    parser.add_argument('--metrics', type=str, default='data/results/stability_metrics.csv',
                      help='Path to stability metrics CSV')
    parser.add_argument('--latency', type=str, default='data/results/aggregated.csv',
                      help='Path to aggregated latency CSV')
    parser.add_argument('--output', type=str, default=None,
                      help='Output path for the plot (default: auto-generated based on mode)')
    
    args = parser.parse_args()
    
    # Set default output paths if not provided
    if args.output is None:
        if args.mode == 'exploration':
            args.output = 'data/results/pareto_frontier_exploration.png'
        else:
            args.output = 'data/results/pareto_frontier_final.png'
    
    # Ensure output directory exists
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    
    if args.mode == 'exploration':
        generate_pareto_exploration(args.metrics, args.latency, args.output)
    else:
        generate_pareto_final(args.metrics, args.latency, args.output)

if __name__ == '__main__':
    main()