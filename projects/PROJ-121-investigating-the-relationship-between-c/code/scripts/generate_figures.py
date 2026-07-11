"""
Script to generate figures for the US3 report: time-series, heatmaps, and periodograms.
This script loads processed data and statistical results to create publication-quality plots.
"""
import os
import sys
import logging
import argparse
from pathlib import Path
from datetime import datetime

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.colors import LogNorm
from scipy import stats

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.utils import get_logger
from src.config import DEFAULT_BIN_SIZE_DAYS

# Configure logging
logger = get_logger(__name__)

# Constants
FIGURES_DIR = project_root / "data" / "results" / "figures"
TIMESERIES_CSV = project_root / "data" / "results" / "dipole_timeseries.csv"
CORRELATION_JSON = project_root / "data" / "results" / "correlation_analysis.json"

def ensure_directories():
    """Ensure the figures directory exists."""
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured figures directory exists: {FIGURES_DIR}")

def load_timeseries_data():
    """Load the dipole timeseries data from CSV."""
    if not TIMESERIES_CSV.exists():
        raise FileNotFoundError(f"Timeseries data not found at {TIMESERIES_CSV}. "
                                "Run the pipeline first to generate this file.")
    
    df = pd.read_csv(TIMESERIES_CSV)
    
    # Convert interval_start to datetime if it's a float (Julian date) or string
    if 'interval_start' in df.columns:
        # Assume Julian Date if float, otherwise parse string
        if pd.api.types.is_numeric_dtype(df['interval_start']):
            # Convert Julian Date to datetime
            # JD 2451545.0 is Jan 1, 2000 12:00:00 UTC
            df['datetime'] = pd.to_datetime(df['interval_start'], unit='D', origin='julian')
        else:
            df['datetime'] = pd.to_datetime(df['interval_start'])
    
    return df

def load_correlation_results():
    """Load correlation analysis results from JSON."""
    if not CORRELATION_JSON.exists():
        logger.warning(f"Correlation results not found at {CORRELATION_JSON}. "
                       "Skipping correlation-based plots.")
        return None
    
    import json
    with open(CORRELATION_JSON, 'r') as f:
        return json.load(f)

def plot_time_series(df, output_path):
    """
    Generate a time-series plot of dipole amplitude and phase over time.
    """
    if df is None or df.empty:
        logger.error("No data provided for time-series plot.")
        return

    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax1 = plt.subplots(figsize=(12, 6))

    # Plot Dipole Amplitude
    color = 'tab:blue'
    ax1.set_xlabel('Date')
    ax1.set_ylabel('Dipole Amplitude ($10^{-3}$)', color=color)
    ax1.plot(df['datetime'], df['dipole_amp'], color=color, marker='o', label='Dipole Amplitude')
    ax1.tick_params(axis='y', labelcolor=color)
    ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:.2f}'))

    # Create a second y-axis for Phase
    ax2 = ax1.twinx()
    color = 'tab:orange'
    ax2.set_ylabel('Dipole Phase (degrees)', color=color)
    ax2.plot(df['datetime'], df['dipole_phase'], color=color, marker='s', linestyle='--', label='Dipole Phase')
    ax2.tick_params(axis='y', labelcolor=color)
    ax2.set_ylim(0, 360)

    # Formatting
    plt.title(f'Dipole Anisotropy Time Series (Bin Size: {DEFAULT_BIN_SIZE_DAYS} days)')
    fig.tight_layout()
    
    # Format x-axis dates
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    ax1.xaxis.set_major_locator(mdates.MonthLocator(interval=6))
    plt.xticks(rotation=45)

    # Save
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Time-series plot saved to {output_path}")

def plot_periodogram(times, amplitudes, output_path, title_suffix=""):
    """
    Generate a Lomb-Scargle periodogram plot.
    Expects times (in days) and amplitudes.
    """
    if times is None or amplitudes is None or len(times) == 0:
        logger.warning("No data provided for periodogram plot.")
        return

    # Calculate Lomb-Scargle using scipy
    # Note: times should be in days, frequencies in cycles/day
    freq, power = stats.lombscargle(times, amplitudes)
    
    # Convert frequency to period (days)
    periods = 1.0 / freq
    
    # Sort by period for plotting
    sorted_indices = np.argsort(periods)
    periods = periods[sorted_indices]
    power = power[sorted_indices]

    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(figsize=(10, 6))

    ax.semilogx(periods, power, color='tab:green', linewidth=1.5)
    ax.set_xlabel('Period (days)')
    ax.set_ylabel('Power')
    ax.set_title(f'Lomb-Scargle Periodogram {title_suffix}')
    
    # Highlight solar cycle period (~11 years = ~4000 days) and 1 year
    ax.axvline(x=365.25, color='red', linestyle='--', alpha=0.5, label='1 Year')
    ax.axvline(x=4015, color='purple', linestyle='--', alpha=0.5, label='~11 Year Solar Cycle')
    ax.legend()

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Periodogram plot saved to {output_path}")

def plot_correlation_heatmap(correlation_matrix, labels, output_path):
    """
    Generate a heatmap of correlation coefficients.
    """
    if correlation_matrix is None:
        logger.warning("No correlation matrix provided for heatmap.")
        return

    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(figsize=(8, 6))

    im = ax.imshow(correlation_matrix, cmap='coolwarm', vmin=-1, vmax=1)
    
    # Set ticks and labels
    ax.set_xticks(np.arange(len(labels)))
    ax.set_yticks(np.arange(len(labels)))
    ax.set_xticklabels(labels)
    ax.set_yticklabels(labels)

    # Rotate the x-axis labels if there are many
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")

    # Loop over data dimensions and create text annotations.
    for i in range(len(labels)):
        for j in range(len(labels)):
            text = ax.text(j, i, f'{correlation_matrix[i, j]:.2f}',
                           ha="center", va="center", color="black")

    ax.set_title('Correlation Coefficient Heatmap')
    fig.colorbar(im, ax=ax, label='Correlation Coefficient')
    plt.tight_layout()

    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Correlation heatmap saved to {output_path}")

def plot_fap_summary(fap_values, output_path):
    """
    Generate a bar chart of False Alarm Probabilities.
    """
    if not fap_values:
        logger.warning("No FAP values provided.")
        return

    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(figsize=(10, 6))

    labels = list(fap_values.keys())
    values = list(fap_values.values())

    bars = ax.bar(labels, values, color='tab:purple')
    ax.set_ylabel('False Alarm Probability (FAP)')
    ax.set_title('Significance of Correlation (FAP)')
    
    # Add a horizontal line for significance threshold (e.g., 0.05 or Bonferroni corrected)
    ax.axhline(y=0.05, color='red', linestyle='--', label='Significance Threshold (0.05)')
    ax.legend()

    # Rotate labels if needed
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right")

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"FAP summary plot saved to {output_path}")

def generate_all_figures():
    """Main function to orchestrate figure generation."""
    logger.info("Starting figure generation...")
    ensure_directories()

    # 1. Load Data
    try:
        df = load_timeseries_data()
        logger.info(f"Loaded {len(df)} rows from timeseries data.")
    except FileNotFoundError as e:
        logger.error(str(e))
        return False

    # 2. Generate Time-Series Plot
    ts_output = FIGURES_DIR / "dipole_timeseries.png"
    plot_time_series(df, ts_output)

    # 3. Prepare data for Periodogram
    # We need time (in days from start) and amplitude
    if 'datetime' in df.columns:
        # Convert to days relative to first observation
        start_date = df['datetime'].min()
        times_days = (df['datetime'] - start_date).dt.total_seconds() / 86400.0
        amplitudes = df['dipole_amp'].values
        
        periodogram_output = FIGURES_DIR / "lomb_scargle_periodogram.png"
        plot_periodogram(times_days, amplitudes, periodogram_output)

    # 4. Load Correlation Results for Heatmap/FAP
    corr_data = load_correlation_results()
    if corr_data:
        # Extract correlation matrix and labels if available
        # Assuming structure: {"IceCube": {"matrix": [...], "labels": [...]}, ...}
        # Or a combined matrix. We'll try to find a 'matrix' key.
        
        # Fallback: If specific structure not found, try to construct from raw data if possible
        # For now, we assume the JSON contains a 'correlation_matrix' and 'labels'
        if 'correlation_matrix' in corr_data and 'labels' in corr_data:
            matrix = np.array(corr_data['correlation_matrix'])
            labels = corr_data['labels']
            heatmap_output = FIGURES_DIR / "correlation_heatmap.png"
            plot_correlation_heatmap(matrix, labels, heatmap_output)

        if 'fap_values' in corr_data:
            fap_output = FIGURES_DIR / "fap_summary.png"
            plot_fap_summary(corr_data['fap_values'], fap_output)
    else:
        logger.info("Skipping correlation heatmap and FAP plots as no correlation results were found.")

    logger.info("Figure generation completed successfully.")
    return True

def main():
    parser = argparse.ArgumentParser(description="Generate figures for the research report.")
    parser.add_argument('--output-dir', type=str, default=None,
                        help='Directory to save figures (default: data/results/figures)')
    
    args = parser.parse_args()
    
    if args.output_dir:
        global FIGURES_DIR
        FIGURES_DIR = Path(args.output_dir)
    
    success = generate_all_figures()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()