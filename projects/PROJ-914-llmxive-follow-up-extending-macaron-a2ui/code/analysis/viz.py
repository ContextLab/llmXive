"""
Visualization module for generating Pareto frontier plots and alignment analysis.
Generates real plots from real simulation data.
"""
import os
import sys
import json
import argparse
import logging
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional

# Conditionally import plotting libraries to handle environments without display
# but ensure the logic runs for CI (saving to disk)
try:
    import matplotlib
    # Use non-interactive backend for headless environments (CI, servers)
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import seaborn as sns
    PLOT_AVAILABLE = True
except ImportError:
    PLOT_AVAILABLE = False
    plt = None
    sns = None
    logging.warning("Matplotlib/Seaborn not available. Plotting functions will raise errors if called.")

import pandas as pd
import numpy as np

from config import get_figures_path, ensure_dirs

# Setup logging
logger = logging.getLogger(__name__)

def load_metrics_data(input_path: str) -> pd.DataFrame:
    """
    Load simulation results from CSV.
    Expects columns: 'latency_ms', 'alignment_score', 'density_level', 'ui_element_count' (optional).
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    
    required_cols = ['latency_ms', 'alignment_score']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Input CSV missing required columns: {missing}")
    
    logger.info(f"Loaded {len(df)} rows from {input_path}")
    return df

def calculate_pareto_frontier(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate the Pareto frontier for Alignment vs Latency.
    Since we want High Alignment and Low Latency, a point (lat, align) is Pareto optimal
    if there is no other point (lat', align') such that lat' <= lat AND align' >= align
    with at least one strict inequality.
    """
    if df.empty:
        return pd.DataFrame(columns=['latency_ms', 'alignment_score'])

    # Sort by latency ascending, then alignment descending
    # This helps in the linear scan to find the frontier
    sorted_df = df.sort_values(by=['latency_ms', 'alignment_score'], ascending=[True, False]).reset_index(drop=True)
    
    pareto_points = []
    current_max_align = -np.inf
    
    # Iterate through sorted points
    # If a point has higher alignment than the current max seen so far (for lower/equal latency),
    # it is on the frontier.
    for _, row in sorted_df.iterrows():
        lat = row['latency_ms']
        align = row['alignment_score']
        
        # A point is Pareto optimal if its alignment is strictly greater than the max alignment
        # of all points with lower or equal latency (since we sorted by latency asc).
        # Actually, standard definition: No other point dominates it.
        # Dominance: A dominates B if A.lat <= B.lat AND A.align >= B.align (and A != B).
        # Since we sorted by latency asc, any previous point has lat' <= current.lat.
        # If previous max_align >= current.align, then that previous point dominates current.
        # So current is only on frontier if align > current_max_align.
        
        if align > current_max_align:
            pareto_points.append({'latency_ms': lat, 'alignment_score': align})
            current_max_align = align
    
    pareto_df = pd.DataFrame(pareto_points)
    # Sort back by latency for plotting
    pareto_df = pareto_df.sort_values(by='latency_ms').reset_index(drop=True)
    
    logger.info(f"Identified {len(pareto_df)} points on the Pareto frontier")
    return pareto_df

def plot_pareto_frontier(
    df: pd.DataFrame, 
    output_path: str, 
    title: str = "Pareto Frontier: Alignment vs Latency",
    xlabel: str = "Latency (ms)",
    ylabel: str = "Alignment Score"
) -> str:
    """
    Generate a Pareto frontier plot.
    Plots all points and highlights the frontier.
    """
    if not PLOT_AVAILABLE:
        raise RuntimeError("Matplotlib/Seaborn not installed. Cannot generate plot.")
    
    ensure_dirs(os.path.dirname(output_path))
    
    pareto_df = calculate_pareto_frontier(df)
    
    if pareto_df.empty:
        logger.warning("No Pareto points found. Cannot generate plot.")
        # Create a minimal empty plot to avoid crash if required
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.text(0.5, 0.5, 'No Data Available', transform=ax.transAxes, ha='center')
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        return output_path

    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Plot all data points (light gray)
    ax.scatter(
        df['latency_ms'], 
        df['alignment_score'], 
        alpha=0.4, 
        color='gray', 
        s=40, 
        label='Simulated Configurations'
    )
    
    # Plot Pareto frontier (highlighted)
    ax.plot(
        pareto_df['latency_ms'], 
        pareto_df['alignment_score'], 
        color='red', 
        linewidth=2.5, 
        marker='o', 
        markersize=6,
        label='Pareto Frontier'
    )
    
    # Annotate the "knee" or specific points if needed, but basic plot first
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.set_xlabel(xlabel, fontsize=12)
    ax.set_ylabel(ylabel, fontsize=12)
    ax.legend(loc='lower right')
    
    # Invert x-axis if we want latency to go left-to-right as "cost" increasing?
    # Usually latency increases rightward. Alignment increases upward.
    # We want bottom-left to be bad, top-left to be good (low latency, high align).
    # So the frontier should curve from top-left to bottom-right.
    # The plot above does exactly that.
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Pareto frontier plot saved to {output_path}")
    return output_path

def plot_alignment_by_density(
    df: pd.DataFrame,
    output_path: str,
    title: str = "Alignment Scores by Information Density",
    xlabel: str = "Latency (ms)",
    ylabel: str = "Alignment Score"
) -> str:
    """
    Plot alignment scores grouped by density level.
    """
    if not PLOT_AVAILABLE:
        raise RuntimeError("Matplotlib/Seaborn not installed. Cannot generate plot.")
    
    ensure_dirs(os.path.dirname(output_path))
    
    if 'density_level' not in df.columns:
        logger.warning("Column 'density_level' not found in data. Falling back to simple scatter.")
        # Fallback: simple scatter without hue
        plt.style.use('seaborn-v0_8-whitegrid')
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.scatter(df['latency_ms'], df['alignment_score'], alpha=0.6, color='blue')
        ax.set_title(title)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        return output_path

    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Use seaborn for better categorical plotting
    sns.scatterplot(
        data=df,
        x='latency_ms',
        y='alignment_score',
        hue='density_level',
        palette='viridis',
        alpha=0.7,
        s=60,
        ax=ax,
        legend='full'
    )
    
    # Add trend lines per density if enough points
    for density in df['density_level'].unique():
        subset = df[df['density_level'] == density]
        if len(subset) > 1:
            z = np.polyfit(subset['latency_ms'], subset['alignment_score'], 1)
            p = np.poly1d(z)
            # Sort x for smooth line
            x_line = np.linspace(subset['latency_ms'].min(), subset['latency_ms'].max(), 100)
            ax.plot(x_line, p(x_line), '--', alpha=0.6, color='gray', linewidth=1)
    
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.set_xlabel(xlabel, fontsize=12)
    ax.set_ylabel(ylabel, fontsize=12)
    ax.legend(title='Density Level')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Alignment by density plot saved to {output_path}")
    return output_path

def main():
    parser = argparse.ArgumentParser(description="Generate Pareto frontier and alignment plots.")
    parser.add_argument('--input', type=str, required=True, help='Path to input CSV (simulation results)')
    parser.add_argument('--output', type=str, required=True, help='Path to output plot (PNG)')
    parser.add_argument('--type', type=str, choices=['pareto', 'density'], default='pareto',
                        help='Type of plot to generate: pareto (default) or density')
    
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    try:
        df = load_metrics_data(args.input)
        
        if args.type == 'pareto':
            output = plot_pareto_frontier(df, args.output)
        elif args.type == 'density':
            output = plot_alignment_by_density(df, args.output)
        else:
            raise ValueError(f"Unknown plot type: {args.type}")
        
        print(f"Success: Plot generated at {output}")
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Data validation error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
