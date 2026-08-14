"""
Visualization module for Cosmic Ray Composition and Solar Activity analysis.

Generates time-lag correlation plots and heatmaps based on the merged
correlation results from T020 (data/processed/correlation_results.csv).

Produces:
  - figures/correlation_heatmap_ratios.png
  - figures/correlation_heatmap_fluxes.png
  - figures/lag_scan_he_p.png
  - figures/lag_scan_fe_p.png
  - figures/lag_scan_absolute_fluxes.png
"""
import os
import sys
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Ensure output directory exists
FIGURES_DIR = Path("figures")
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

# Input file from T020
INPUT_FILE = Path("data/processed/correlation_results.csv")

def load_correlation_results() -> pd.DataFrame:
    """
    Load the merged correlation results from T020.
    
    Expects columns: 
    - metric_type (e.g., 'He/p', 'Fe/p', 'He_flux', 'Fe_flux')
    - rigidity_bin (float or string representing bin)
    - lag_months (int)
    - correlation (float)
    - p_value (float)
    """
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Input file {INPUT_FILE} not found. "
            "Ensure T020 (correlation analysis) has been run successfully."
        )
    
    df = pd.read_csv(INPUT_FILE)
    
    # Ensure numeric types
    if 'lag_months' in df.columns:
        df['lag_months'] = pd.to_numeric(df['lag_months'], errors='coerce')
    if 'correlation' in df.columns:
        df['correlation'] = pd.to_numeric(df['correlation'], errors='coerce')
    if 'p_value' in df.columns:
        df['p_value'] = pd.to_numeric(df['p_value'], errors='coerce')
    
    logger.info(f"Loaded {len(df)} correlation records from {INPUT_FILE}")
    return df

def plot_heatmap(df: pd.DataFrame, metric_type: str, output_path: Path, title: str):
    """
    Generate a heatmap of correlation coefficients vs. rigidity bin and lag months.
    """
    # Filter for specific metric type
    subset = df[df['metric_type'] == metric_type].copy()
    
    if subset.empty:
        logger.warning(f"No data found for metric_type '{metric_type}' in heatmap.")
        return

    # Pivot table for heatmap: Rows=Rigidity, Cols=Lag, Values=Correlation
    # Handle rigidity_bin as string or numeric for pivoting
    pivot_data = subset.pivot_table(
        index='rigidity_bin', 
        columns='lag_months', 
        values='correlation', 
        aggfunc='first'
    )
    
    # Sort columns (lags) numerically
    try:
        pivot_data = pivot_data.sort_index(axis=1, key=lambda x: x.astype(float))
    except (ValueError, TypeError):
        # If rigidity is not numeric, sort as string
        pass

    plt.figure(figsize=(12, 8))
    sns.heatmap(
        pivot_data, 
        cmap='RdBu_r', 
        center=0, 
        annot=True, 
        fmt=".2f", 
        cbar_kws={'label': 'Correlation Coefficient'},
        linewidths=.5
    )
    plt.title(title)
    plt.xlabel('Lag (Months)')
    plt.ylabel('Rigidity Bin')
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    logger.info(f"Saved heatmap to {output_path}")

def plot_lag_scan(df: pd.DataFrame, metric_type: str, output_path: Path, title: str):
    """
    Generate a line plot of correlation vs. lag months for a specific metric type.
    Plots multiple lines for different rigidity bins.
    """
    subset = df[df['metric_type'] == metric_type].copy()
    
    if subset.empty:
        logger.warning(f"No data found for metric_type '{metric_type}' in lag scan.")
        return

    plt.figure(figsize=(14, 8))
    
    # Group by rigidity bin
    rigidity_bins = subset['rigidity_bin'].unique()
    
    for rig in rigidity_bins:
        bin_data = subset[subset['rigidity_bin'] == rig].sort_values('lag_months')
        plt.plot(
            bin_data['lag_months'], 
            bin_data['correlation'], 
            marker='o', 
            label=f'Rigidity: {rig}'
        )
    
    plt.axhline(0, color='black', linewidth=0.8, linestyle='--')
    plt.title(title)
    plt.xlabel('Lag (Months)')
    plt.ylabel('Correlation Coefficient')
    plt.legend(title='Rigidity Bin')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    logger.info(f"Saved lag scan plot to {output_path}")

def generate_all_plots(df: pd.DataFrame):
    """
    Orchestrates the generation of all required visualization artifacts.
    """
    # 1. Heatmaps
    plot_heatmap(
        df, 
        'He/p', 
        FIGURES_DIR / 'correlation_heatmap_ratios.png', 
        'He/p Composition Ratio: Correlation vs. Rigidity & Lag'
    )
    
    # We assume T020 outputs 'Fe/p' if available, otherwise skip gracefully
    if 'Fe/p' in df['metric_type'].values:
        plot_heatmap(
            df, 
            'Fe/p', 
            FIGURES_DIR / 'correlation_heatmap_heavies.png', 
            'Fe/p Composition Ratio: Correlation vs. Rigidity & Lag'
        )
    
    # Heatmap for absolute fluxes (control analysis)
    # Assuming metric_type for absolute fluxes follows a pattern like 'He_flux' or similar
    # We'll try to detect available flux types dynamically or use a generic label
    flux_metrics = [m for m in df['metric_type'].unique() if 'flux' in str(m).lower()]
    
    if flux_metrics:
        # If multiple flux types exist, we might need to aggregate or pick one.
        # For this task, we'll plot the first one found as 'Absolute Fluxes'
        # or create a combined view if the data structure allows.
        # Given the T020 description, it likely outputs specific bins.
        # Let's create a heatmap for the first flux metric found.
        flux_type = flux_metrics[0]
        plot_heatmap(
            df, 
            flux_type, 
            FIGURES_DIR / 'correlation_heatmap_fluxes.png', 
            f'Absolute Flux ({flux_type}): Correlation vs. Rigidity & Lag'
        )
    else:
        logger.warning("No absolute flux metrics found in data for heatmap.")

    # 2. Lag Scans
    plot_lag_scan(
        df, 
        'He/p', 
        FIGURES_DIR / 'lag_scan_he_p.png', 
        'He/p Ratio: Correlation vs. Lag by Rigidity'
    )
    
    if 'Fe/p' in df['metric_type'].values:
        plot_lag_scan(
            df, 
            'Fe/p', 
            FIGURES_DIR / 'lag_scan_fe_p.png', 
            'Fe/p Ratio: Correlation vs. Lag by Rigidity'
        )
    
    # Lag scan for absolute fluxes
    if flux_metrics:
        flux_type = flux_metrics[0]
        plot_lag_scan(
            df, 
            flux_type, 
            FIGURES_DIR / 'lag_scan_absolute_fluxes.png', 
            f'Absolute Flux ({flux_type}): Correlation vs. Lag by Rigidity'
        )

def main():
    """
    Entry point for the visualization pipeline.
    """
    logger.info("Starting visualization pipeline (T022)...")
    
    try:
        df = load_correlation_results()
        generate_all_plots(df)
        logger.info("Visualization pipeline completed successfully.")
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    except Exception as e:
        logger.error(f"An error occurred during visualization: {e}")
        raise

if __name__ == "__main__":
    main()
