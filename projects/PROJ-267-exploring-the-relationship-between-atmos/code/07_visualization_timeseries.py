"""
Time-series visualization for Atmospheric River Gravity Correlation.

Generates a time-series overlay plot of Gravity Anomalies and AR Intensity
to visualize their temporal relationship.

Input: data/processed/merged_monthly.csv (from T017)
Output: output/timeseries_overlay.png
"""
import os
import sys
import logging
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
INPUT_PATH = PROJECT_ROOT / "data" / "processed" / "merged_monthly.csv"
OUTPUT_DIR = PROJECT_ROOT / "output"
OUTPUT_PATH = OUTPUT_DIR / "timeseries_overlay.png"

def load_merged_data():
    """Load the merged monthly dataset."""
    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"Input file not found: {INPUT_PATH}. "
            "Please ensure T017 (03_merge_output.py) has been run successfully."
        )
    
    df = pd.read_csv(INPUT_PATH)
    
    # Ensure date column is datetime
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
    elif 'month' in df.columns:
        # Handle if month is string like "2018-01"
        df['date'] = pd.to_datetime(df['month'])
        df = df.sort_values('date')
    
    logger.info(f"Loaded {len(df)} rows from {INPUT_PATH}")
    return df

def plot_timeseries(df, output_path):
    """
    Generate time-series overlay plot.
    
    Plots:
    1. Gravity Anomaly (left y-axis)
    2. AR Integrated Water Vapor Transport (right y-axis)
    
    Saves the figure to output_path.
    """
    if df.empty:
        raise ValueError("DataFrame is empty. Cannot generate plot.")
    
    # Identify columns dynamically if exact names vary slightly
    # Expected columns based on T017: 'date', 'gravity_anomaly', 'ar_iwv_transport' (or similar)
    gravity_col = None
    ar_col = None
    
    cols = df.columns.tolist()
    for c in cols:
        if 'gravity' in c.lower() and 'anomaly' in c.lower():
            gravity_col = c
        elif 'ar' in c.lower() and ('iwv' in c.lower() or 'transport' in c.lower()):
            ar_col = c
    
    if not gravity_col or not ar_col:
        raise ValueError(
            f"Could not identify required columns. "
            f"Available columns: {cols}. "
            f"Expected gravity anomaly and AR transport columns."
        )
    
    # Create figure and primary axis
    fig, ax1 = plt.subplots(figsize=(14, 7))
    
    # Plot Gravity Anomaly
    color_gravity = '#2c7bb6'
    ax1.set_xlabel('Date', fontsize=12)
    ax1.set_ylabel('Gravity Anomaly (μGal)', color=color_gravity, fontsize=12)
    ax1.plot(df['date'], df[gravity_col], color=color_gravity, label='Gravity Anomaly', linewidth=2, marker='o', markersize=4)
    ax1.tick_params(axis='y', labelcolor=color_gravity)
    ax1.grid(True, which='both', linestyle='--', alpha=0.5)
    
    # Create secondary axis for AR Intensity
    ax2 = ax1.twinx()
    color_ar = '#d7191c'
    ax2.set_ylabel('AR IWV Transport (kg/m/s)', color=color_ar, fontsize=12)
    ax2.plot(df['date'], df[ar_col], color=color_ar, label='AR IWV Transport', linewidth=2, marker='s', markersize=4, alpha=0.7)
    ax2.tick_params(axis='y', labelcolor=color_ar)
    
    # Combine legends
    lines_1, labels_1 = ax1.get_legend_handles_labels()
    lines_2, labels_2 = ax2.get_legend_handles_labels()
    ax1.legend(lines_1 + lines_2, labels_1 + labels_2, loc='upper left', frameon=True, shadow=True)
    
    # Format x-axis dates
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    ax1.xaxis.set_major_locator(mdates.MonthLocator(interval=6))
    plt.xticks(rotation=45)
    
    # Title and layout
    plt.title('Time-Series Overlay: Gravity Anomaly vs. Atmospheric River Intensity', fontsize=14, fontweight='bold')
    fig.tight_layout()
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save figure
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    
    logger.info(f"Time-series plot saved to {output_path}")

def main():
    """Main entry point."""
    try:
        logger.info("Starting time-series visualization generation...")
        df = load_merged_data()
        plot_timeseries(df, OUTPUT_PATH)
        logger.info("Visualization generation completed successfully.")
        return 0
    except Exception as e:
        logger.error(f"Failed to generate visualization: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())