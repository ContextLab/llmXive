import os
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from code.config import ACE_VARS, NOAA_VARS
from code import logger
from code.analysis.correlation import load_synced_data

# Ensure output directories exist
FIGURES_DIR = "artifacts/figures"
os.makedirs(FIGURES_DIR, exist_ok=True)

def plot_time_series_overlay(df: pd.DataFrame, output_path: str, params: Optional[List[str]] = None):
    """
    Generate a time-series overlay plot for ACE parameters and NOAA indices.
    
    Args:
        df: Synced dataframe with 'timestamp' and variables.
        output_path: Path to save the PNG.
        params: List of variable names to plot (defaults to ACE_VARS).
    """
    if params is None:
        params = ACE_VARS + NOAA_VARS
    
    # Filter available columns
    available_params = [p for p in params if p in df.columns]
    if not available_params:
        logger.warning(f"No matching parameters found in dataframe for plotting. Available: {df.columns.tolist()}")
        return

    plt.figure(figsize=(14, 8))
    
    # Normalize data for overlay if ranges differ significantly
    # Simple approach: plot raw values but use secondary axis if needed, 
    # or just plot them all if they are somewhat comparable (e.g. normalized)
    # For this specific task, we plot raw values but might need dual axes for Dst/Kp vs Density/Temp
    
    # Separate ACE and NOAA for potential dual axis handling
    ace_vars = [v for v in available_params if v in ACE_VARS]
    noaa_vars = [v for v in available_params if v in NOAA_VARS]
    
    if ace_vars:
        ax1 = plt.gca()
        ax1.set_xlabel('Time')
        ax1.set_ylabel('ACE Parameters', color='tab:blue')
        for var in ace_vars:
            ax1.plot(df['timestamp'], df[var], label=var, alpha=0.7)
        ax1.tick_params(axis='y', labelcolor='tab:blue')
        ax1.grid(True, alpha=0.3)
    
    if noaa_vars:
        ax2 = ax1.twinx() if ace_vars else plt.gca()
        ax2.set_ylabel('NOAA Indices', color='tab:red')
        for var in noaa_vars:
            ax2.plot(df['timestamp'], df[var], label=var, linestyle='--', alpha=0.7)
        ax2.tick_params(axis='y', labelcolor='tab:red')
    
    plt.title('Solar Wind Composition & Geomagnetic Indices Time Series')
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    # Combine legends from both axes
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels() if noaa_vars else ([], [])
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
    
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    logger.info(f"Saved time-series plot to {output_path}")

def plot_correlation_heatmap(correlation_results: pd.DataFrame, output_path: str):
    """
    Generate a correlation heatmap (parameters × lags) for the full dataset.
    
    Args:
        correlation_results: DataFrame containing correlation statistics.
                            Expected columns: 'ace_var', 'noaa_var', 'lag_hours', 'pearson_r', 'spearman_rho', 'p_value_bonferroni'.
        output_path: Path to save the PNG.
    """
    logger.info(f"Generating correlation heatmap for {len(correlation_results)} pairs")
    
    # Pivot the data to create a matrix for heatmap
    # We will plot Pearson R. Rows: ACE vars, Columns: Lags (for a specific NOAA var or combined?)
    # The task asks for "parameters × lags". Usually this implies a grid of (ACE_VAR, NOAA_VAR) x LAG.
    # To keep it readable, we might create a multi-index or separate plots per NOAA var.
    # Given the constraint of a single heatmap, let's try to structure it as:
    # Rows: ACE_VAR + NOAA_VAR (e.g., "N_p - Kp")
    # Cols: Lags
    
    if 'pearson_r' not in correlation_results.columns:
        logger.error("Correlation results must contain 'pearson_r' column for heatmap.")
        return

    # Ensure lag_hours is numeric and sorted
    correlation_results = correlation_results.copy()
    correlation_results['lag_hours'] = pd.to_numeric(correlation_results['lag_hours'], errors='coerce')
    
    # Create a unique identifier for the Y-axis (Parameter Pair)
    correlation_results['pair_label'] = correlation_results['ace_var'].astype(str) + ' vs ' + correlation_results['noaa_var'].astype(str)
    
    # Pivot table: Rows = Pair, Cols = Lag, Values = Pearson R
    heatmap_data = correlation_results.pivot_table(
        index='pair_label', 
        columns='lag_hours', 
        values='pearson_r',
        aggfunc='first' # Should be unique per pair-lag
    )
    
    # Sort lags numerically
    heatmap_data = heatmap_data.sort_index(axis=1, key=lambda x: x.astype(float))
    
    plt.figure(figsize=(12, max(8, len(heatmap_data) * 0.5)))
    
    # Use a diverging colormap centered at 0
    cmap = plt.cm.RdBu_r
    vmin = -1.0
    vmax = 1.0
    
    im = plt.imshow(heatmap_data.values, cmap=cmap, aspect='auto', vmin=vmin, vmax=vmax, origin='upper')
    
    # Set ticks and labels
    plt.yticks(range(len(heatmap_data.index)), heatmap_data.index, fontsize=10)
    plt.xticks(range(len(heatmap_data.columns)), [str(int(lag)) + 'h' if not np.isnan(lag) else 'NaN' for lag in heatmap_data.columns], fontsize=10)
    
    # Add colorbar
    cbar = plt.colorbar(im, shrink=0.8)
    cbar.set_label('Pearson Correlation (r)', rotation=270, labelpad=20)
    
    # Annotate cells with values
    for i in range(len(heatmap_data.index)):
        for j in range(len(heatmap_data.columns)):
            val = heatmap_data.values[i, j]
            if not np.isnan(val):
                plt.text(j, i, f"{val:.2f}", ha="center", va="center", color="black" if abs(val) < 0.3 else "white", fontsize=8)
    
    plt.title('Correlation Heatmap: Solar Wind Parameters vs Geomagnetic Indices (Lagged)', fontsize=14)
    plt.xlabel('Lag (hours)')
    plt.ylabel('Variable Pair (ACE vs NOAA)')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    logger.info(f"Saved correlation heatmap to {output_path}")

def generate_all_lag_plots(df: pd.DataFrame, output_dir: str = FIGURES_DIR):
    """
    Generate individual time-series plots for specific lag combinations if needed,
    or orchestrate the main visualization pipeline.
    """
    # Placeholder for specific lag plots if required by other tasks
    pass

def run_viz_pipeline(data_path: str = "data/processed/synced.csv", 
                     correlation_path: str = "data/processed/correlation_results.csv"):
    """
    Main entry point for the visualization pipeline (US3).
    
    1. Loads synced data.
    2. Generates time-series overlay.
    3. Loads correlation results and generates heatmap.
    
    Args:
        data_path: Path to the synced CSV.
        correlation_path: Path to the correlation results CSV.
    """
    logger.info("Starting visualization pipeline...")
    
    # 1. Time Series Plot
    if os.path.exists(data_path):
        df = load_synced_data(data_path)
        ts_output = os.path.join(FIGURES_DIR, "time_series_overlay.png")
        plot_time_series_overlay(df, ts_output)
    else:
        logger.warning(f"Synced data not found at {data_path}. Skipping time series plot.")
    
    # 2. Correlation Heatmap
    if os.path.exists(correlation_path):
        corr_df = pd.read_csv(correlation_path)
        heatmap_output = os.path.join(FIGURES_DIR, "correlation_heatmap.png")
        plot_correlation_heatmap(corr_df, heatmap_output)
    else:
        logger.warning(f"Correlation results not found at {correlation_path}. Skipping heatmap.")
    
    logger.info("Visualization pipeline completed.")

if __name__ == "__main__":
    # Execute the pipeline if run directly
    run_viz_pipeline()