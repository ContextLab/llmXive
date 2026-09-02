"""
Plotting utilities for generating timescale-accuracy curves.

Implements T017: Generate timescale-accuracy curves (MAE vs. Duration) with uncertainty bands.
"""
import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Import project utilities
from utils.logging import get_logger

logger = get_logger(__name__)

# Set style for publication-quality plots
sns.set_theme(style="whitegrid", context="paper")
plt.rcParams['font.size'] = 10
plt.rcParams['axes.linewidth'] = 1.0
plt.rcParams['xtick.major.width'] = 1.0
plt.rcParams['ytick.major.width'] = 1.0

@dataclass
class PlotConfig:
    """Configuration for plotting."""
    output_dir: Path
    figsize: Tuple[int, int] = (10, 6)
    dpi: int = 300
    style: str = "whitegrid"
    palette: str = "muted"
    title: str = "Timescale-Accuracy Curves"
    xlabel: str = "Simulation Duration (ns)"
    ylabel: str = "Mean Absolute Error (MAE) in D (nm²/ns)"
    legend_title: str = "Solvent"
    
def load_diffusion_results(results_path: Path) -> pd.DataFrame:
    """
    Load diffusion results from the processed data directory.
    
    Args:
        results_path: Path to the diffusion results CSV file.
        
    Returns:
        DataFrame containing simulation results with MAE and duration.
        
    Raises:
        FileNotFoundError: If the results file does not exist.
        ValueError: If the file is empty or missing required columns.
    """
    if not results_path.exists():
        raise FileNotFoundError(f"Results file not found: {results_path}")
    
    df = pd.read_csv(results_path)
    
    required_cols = ['solvent', 'duration_ns', 'mae']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in {results_path}: {missing_cols}")
    
    if df.empty:
        raise ValueError(f"Results file {results_path} is empty.")
    
    logger.info(f"Loaded {len(df)} records from {results_path}")
    return df

def calculate_uncertainty_bands(df: pd.DataFrame, duration_col: str = 'duration_ns', 
                                 mae_col: str = 'mae', group_col: str = 'solvent') -> pd.DataFrame:
    """
    Calculate uncertainty bands (mean ± std) for MAE across durations.
    
    Args:
        df: DataFrame with simulation results.
        duration_col: Column name for simulation duration.
        mae_col: Column name for MAE values.
        group_col: Column name for grouping (e.g., solvent).
        
    Returns:
        DataFrame with aggregated statistics per duration per solvent.
    """
    # Group by solvent and duration to calculate stats
    agg_df = df.groupby([group_col, duration_col])[mae_col].agg(['mean', 'std', 'count']).reset_index()
    agg_df.rename(columns={'mean': 'mae_mean', 'std': 'mae_std', 'count': 'n'}, inplace=True)
    
    # Fill NaN std with 0 (single observation)
    agg_df['mae_std'] = agg_df['mae_std'].fillna(0.0)
    
    # Calculate confidence interval (approximate 95% CI using 1.96 * std / sqrt(n))
    agg_df['ci_lower'] = agg_df['mae_mean'] - 1.96 * agg_df['mae_std'] / np.sqrt(agg_df['n'])
    agg_df['ci_upper'] = agg_df['mae_mean'] + 1.96 * agg_df['mae_std'] / np.sqrt(agg_df['n'])
    
    # Ensure non-negative lower bounds
    agg_df['ci_lower'] = agg_df['ci_lower'].clip(lower=0.0)
    
    logger.info(f"Calculated uncertainty bands for {len(agg_df)} groups")
    return agg_df

def generate_timescale_accuracy_plot(df: pd.DataFrame, config: PlotConfig) -> Path:
    """
    Generate the timescale-accuracy curve plot with uncertainty bands.
    
    Creates a plot showing MAE vs. Simulation Duration for each solvent,
    with shaded uncertainty bands representing 95% confidence intervals.
    
    Args:
        df: DataFrame with diffusion results (must have solvent, duration_ns, mae).
        config: Plot configuration object.
        
    Returns:
        Path to the saved plot file.
    """
    # Ensure output directory exists
    config.output_dir.mkdir(parents=True, exist_ok=True)
    
    # Calculate uncertainty bands
    agg_df = calculate_uncertainty_bands(df)
    
    # Create the plot
    fig, ax = plt.subplots(figsize=config.figsize, dpi=config.dpi)
    
    # Plot each solvent with uncertainty band
    solvents = agg_df[config.legend_title].unique()
    
    for solvent in solvents:
        subset = agg_df[agg_df[config.legend_title] == solvent]
        
        # Sort by duration for smooth line drawing
        subset = subset.sort_values('duration_ns')
        
        ax.plot(
            subset['duration_ns'], 
            subset['mae_mean'],
            label=solvent,
            marker='o',
            linewidth=2,
            markersize=6
        )
        
        # Add uncertainty band
        ax.fill_between(
            subset['duration_ns'],
            subset['ci_lower'],
            subset['ci_upper'],
            alpha=0.2
        )
    
    # Labels and title
    ax.set_xlabel(config.xlabel, fontsize=12, fontweight='bold')
    ax.set_ylabel(config.ylabel, fontsize=12, fontweight='bold')
    ax.set_title(config.title, fontsize=14, fontweight='bold')
    
    # Legend
    ax.legend(title=config.legend_title, loc='best', framealpha=0.9)
    
    # Grid and layout
    ax.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    
    # Save plot
    output_path = config.output_dir / "timescale_accuracy_curve.png"
    plt.savefig(output_path, dpi=config.dpi, bbox_inches='tight')
    plt.close(fig)
    
    logger.info(f"Saved timescale-accuracy plot to {output_path}")
    return output_path

def generate_multi_solvent_comparison(df: pd.DataFrame, config: PlotConfig) -> Path:
    """
    Generate a comparison plot showing all solvents on the same axes.
    
    This is an alternative visualization that emphasizes the comparison
    between different solvents across timescales.
    
    Args:
        df: DataFrame with diffusion results.
        config: Plot configuration.
        
    Returns:
        Path to the saved plot file.
    """
    config.output_dir.mkdir(parents=True, exist_ok=True)
    agg_df = calculate_uncertainty_bands(df)
    
    fig, ax = plt.subplots(figsize=config.figsize, dpi=config.dpi)
    
    # Use seaborn's lineplot for automatic handling of error bands
    sns.lineplot(
        data=agg_df,
        x='duration_ns',
        y='mae_mean',
        hue=config.legend_title,
        errorbar=("ci", 95),
        markers=True,
        dashes=False,
        ax=ax,
        linewidth=2,
        markersize=8
    )
    
    ax.set_xlabel(config.xlabel, fontsize=12, fontweight='bold')
    ax.set_ylabel(config.ylabel, fontsize=12, fontweight='bold')
    ax.set_title(f"{config.title}\n(Multi-solvent Comparison)", fontsize=14, fontweight='bold')
    ax.legend(title=config.legend_title, loc='best', framealpha=0.9)
    ax.grid(True, linestyle='--', alpha=0.7)
    
    output_path = config.output_dir / "timescale_accuracy_comparison.png"
    plt.savefig(output_path, dpi=config.dpi, bbox_inches='tight')
    plt.close(fig)
    
    logger.info(f"Saved comparison plot to {output_path}")
    return output_path

def main():
    """
    Main entry point for generating timescale-accuracy plots.
    
    Reads diffusion results from data/processed/diffusion_results.csv
    and generates plots in data/processed/plots/.
    """
    # Define paths relative to project root
    project_root = Path(__file__).resolve().parent.parent.parent
    results_path = project_root / "data" / "processed" / "diffusion_results.csv"
    output_dir = project_root / "data" / "processed" / "plots"
    
    logger.info(f"Starting plot generation for T017")
    logger.info(f"Results path: {results_path}")
    logger.info(f"Output directory: {output_dir}")
    
    try:
        # Load data
        df = load_diffusion_results(results_path)
        
        # Configure plot
        plot_config = PlotConfig(
            output_dir=output_dir,
            figsize=(10, 6),
            dpi=300,
            title="Timescale-Accuracy Curves: MAE vs. Simulation Duration",
            xlabel="Simulation Duration (ns)",
            ylabel="Mean Absolute Error (MAE) in Diffusion Coefficient (nm²/ns)",
            legend_title="Solvent"
        )
        
        # Generate primary plot
        plot_path = generate_timescale_accuracy_plot(df, plot_config)
        logger.info(f"Primary plot generated: {plot_path}")
        
        # Generate comparison plot
        comparison_path = generate_multi_solvent_comparison(df, plot_config)
        logger.info(f"Comparison plot generated: {comparison_path}")
        
        # Log success
        logger.info("T017 completed successfully. All plots generated.")
        
    except FileNotFoundError as e:
        logger.error(f"Data file not found: {e}")
        logger.error("Ensure that T018 (main pipeline) has been run to generate diffusion_results.csv")
        raise
    except ValueError as e:
        logger.error(f"Data validation error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during plot generation: {e}")
        raise

if __name__ == "__main__":
    main()