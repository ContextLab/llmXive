"""
Visualization module for llmXive A2UI study.
Generates Pareto frontier plots and alignment analysis visualizations.
"""
import os
import sys
import json
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
from matplotlib.patches import Patch
from scipy.stats import gaussian_kde

# Configure matplotlib for non-interactive backend (CI/Headless)
matplotlib.use('Agg')

from config import get_figures_path, ensure_dirs
from utils.logging import get_experiment_logger

# Set up logging
logger = get_experiment_logger(__name__)

# Constants for plotting
DENSITY_LABELS = {1: 'Low', 3: 'Medium', 5: 'High', 10: 'Max'}
DENSITY_COLORS = {1: '#1f77b4', 3: '#ff7f0e', 5: '#2ca02c', 10: '#d62728'}
DENSITY_MARKERS = {1: 'o', 3: 's', 5: '^', 10: 'D'}

def load_metrics_data(input_path: str) -> pd.DataFrame:
    """
    Load simulation results from CSV.
    
    Args:
        input_path: Path to the simulation results CSV file.
        
    Returns:
        DataFrame with simulation metrics.
        
    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If required columns are missing.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
        
    df = pd.read_csv(input_path)
    
    required_columns = ['alignment_score', 'total_latency_ms', 'density_level']
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in {input_path}: {missing}")
        
    logger.info(f"Loaded {len(df)} rows from {input_path}")
    return df

def calculate_pareto_frontier(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate the Pareto frontier for Alignment vs. Latency.
    Since we want HIGH alignment and LOW latency, a point A dominates B if:
    A.alignment >= B.alignment AND A.latency <= B.latency, with at least one strict inequality.
    
    Args:
        df: DataFrame with alignment_score and total_latency_ms.
        
    Returns:
        DataFrame containing only the Pareto optimal points.
    """
    if df.empty:
        return pd.DataFrame()
        
    # Sort by latency ascending, then alignment descending
    # This helps in efficient frontier detection
    sorted_df = df.sort_values(by=['total_latency_ms', 'alignment_score'], ascending=[True, False])
    
    pareto_points = []
    max_alignment_so_far = -np.inf
    
    # Since we sorted by latency ascending, we iterate through increasing latency.
    # A point is Pareto optimal if its alignment is strictly better than the max alignment
    # seen at any lower (or equal) latency.
    # Wait, the definition: A dominates B if A.latency <= B.latency AND A.align >= B.align.
    # If we sort by latency ascending:
    # For a point P at index i, if there exists any point j < i (lower latency) with align_j >= align_i,
    # then P is dominated (because j has lower latency and higher/equal alignment).
    # So P is Pareto optimal ONLY IF its alignment is strictly greater than the max alignment of all points with lower latency.
    
    for _, row in sorted_df.iterrows():
        current_latency = row['total_latency_ms']
        current_alignment = row['alignment_score']
        
        if current_alignment > max_alignment_so_far:
            pareto_points.append(row)
            max_alignment_so_far = current_alignment
            
    if not pareto_points:
        return pd.DataFrame()
        
    return pd.DataFrame(pareto_points)

def plot_pareto_frontier(df: pd.DataFrame, frontier_df: pd.DataFrame, output_path: str) -> None:
    """
    Generate the Pareto frontier plot (Alignment vs. Latency).
    
    Args:
        df: Full dataset.
        frontier_df: Pareto optimal points.
        output_path: Path to save the figure.
    """
    plt.figure(figsize=(10, 7))
    
    # Plot all non-frontier points as gray dots
    non_frontier = df[~df.index.isin(frontier_df.index)]
    if not non_frontier.empty:
        plt.scatter(
            non_frontier['total_latency_ms'],
            non_frontier['alignment_score'],
            color='lightgray',
            alpha=0.5,
            label='Sub-optimal',
            s=40
        )
    
    # Plot Pareto frontier points
    if not frontier_df.empty:
        plt.scatter(
            frontier_df['total_latency_ms'],
            frontier_df['alignment_score'],
            color='darkblue',
            marker='o',
            s=80,
            edgecolors='black',
            linewidth=1.5,
            label='Pareto Frontier',
            zorder=5
        )
        
        # Connect frontier points with a line
        sorted_frontier = frontier_df.sort_values('total_latency_ms')
        plt.plot(
            sorted_frontier['total_latency_ms'],
            sorted_frontier['alignment_score'],
            color='darkblue',
            linewidth=2,
            linestyle='--',
            alpha=0.7,
            zorder=4
        )
    
    # Styling
    plt.xlabel('Total Latency (ms)', fontsize=12, fontweight='bold')
    plt.ylabel('Alignment Score', fontsize=12, fontweight='bold')
    plt.title('Pareto Frontier: Alignment vs. Latency', fontsize=14, fontweight='bold')
    plt.grid(True, linestyle=':', alpha=0.6)
    plt.legend(loc='lower right')
    
    # Invert X-axis? No, usually latency increases to the right.
    # But we want LOW latency, so the frontier should curve up and to the left.
    # The plot is standard: X=Latency (low to high), Y=Alignment (low to high).
    # The frontier should be the "top-left" boundary.
    
    plt.tight_layout()
    
    # Ensure directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Pareto frontier plot saved to {output_path}")

def plot_alignment_by_density(df: pd.DataFrame, output_path: str) -> None:
    """
    Plot alignment scores across information density levels.
    
    Args:
        df: DataFrame with alignment_score and density_level.
        output_path: Path to save the figure.
    """
    plt.figure(figsize=(10, 7))
    
    densities = sorted(df['density_level'].unique())
    
    for density in densities:
        subset = df[df['density_level'] == density]
        label = DENSITY_LABELS.get(density, f"Density {density}")
        color = DENSITY_COLORS.get(density, 'gray')
        marker = DENSITY_MARKERS.get(density, 'o')
        
        # Sort by latency for line plot
        subset_sorted = subset.sort_values('total_latency_ms')
        
        plt.scatter(
            subset_sorted['total_latency_ms'],
            subset_sorted['alignment_score'],
            label=f"Density {label} ({density})",
            color=color,
            marker=marker,
            alpha=0.7,
            s=60
        )
        
        # Optional: connect with a faint line to show trend
        plt.plot(
            subset_sorted['total_latency_ms'],
            subset_sorted['alignment_score'],
            color=color,
            alpha=0.3,
            linestyle='-',
            linewidth=1
        )
    
    plt.xlabel('Total Latency (ms)', fontsize=12, fontweight='bold')
    plt.ylabel('Alignment Score', fontsize=12, fontweight='bold')
    plt.title('Alignment Scores by Information Density', fontsize=14, fontweight='bold')
    plt.grid(True, linestyle=':', alpha=0.6)
    plt.legend(loc='lower right')
    plt.tight_layout()
    
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Alignment by density plot saved to {output_path}")

def main():
    """Main entry point for visualization generation."""
    parser = argparse.ArgumentParser(description="Generate visualization plots for A2UI study.")
    parser.add_argument(
        '--input', 
        type=str, 
        required=True,
        help='Path to input simulation results CSV (e.g., data/simulation/results.csv)'
    )
    parser.add_argument(
        '--output', 
        type=str, 
        required=True,
        help='Path to save the Pareto frontier plot (e.g., figures/pareto_frontier.png)'
    )
    parser.add_argument(
        '--density-output',
        type=str,
        default=None,
        help='Path to save the alignment by density plot (optional)'
    )
    
    args = parser.parse_args()
    
    try:
        # Load data
        df = load_metrics_data(args.input)
        
        # Calculate Pareto frontier
        frontier_df = calculate_pareto_frontier(df)
        logger.info(f"Identified {len(frontier_df)} Pareto optimal points out of {len(df)} total.")
        
        # Ensure output directory exists
        output_dir = os.path.dirname(args.output)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        
        # Generate Pareto plot
        plot_pareto_frontier(df, frontier_df, args.output)
        
        # Generate density plot if requested
        if args.density_output:
            plot_alignment_by_density(df, args.density_output)
            
        logger.info("Visualization generation completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Data error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during visualization: {e}")
        raise

if __name__ == '__main__':
    main()
