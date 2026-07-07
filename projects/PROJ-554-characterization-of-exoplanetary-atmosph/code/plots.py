import logging
import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from config import get_config
from utils import setup_logging

# Ensure seaborn style is applied for professional plots
sns.set(style="whitegrid", context="talk", font_scale=1.1)

def load_analysis_data() -> pd.DataFrame:
    """
    Load the processed metadata and detection limits required for the plot.
    Expects data/processed/metadata.csv and data/processed/detection_limits.csv.
    """
    config = get_config()
    metadata_path = config['paths']['processed_metadata']
    detection_limits_path = config['paths']['detection_limits']

    if not os.path.exists(metadata_path):
        raise FileNotFoundError(f"Required metadata file not found: {metadata_path}. "
                                "Run download.py first.")
    if not os.path.exists(detection_limits_path):
        raise FileNotFoundError(f"Required detection limits file not found: {detection_limits_path}. "
                                "Run analysis.py (T035) first.")

    df_meta = pd.read_csv(metadata_path)
    df_det = pd.read_csv(detection_limits_path)

    # Merge on planet name or ID if available, otherwise assume row alignment or merge by index
    # Assuming 'planet_name' or 'planet_id' exists in both. If not, we merge on index.
    common_cols = set(df_meta.columns) & set(df_det.columns)
    if 'planet_name' in common_cols:
        df = pd.merge(df_meta, df_det, on='planet_name', how='inner')
    elif 'planet_id' in common_cols:
        df = pd.merge(df_meta, df_det, on='planet_id', how='inner')
    else:
        # Fallback: assume they are in the same order and merge by index
        logging.warning("No common key found for merge. Assuming row alignment.")
        df = pd.concat([df_meta, df_det], axis=1)

    # Ensure numeric types for SNR and Resolution
    if 'SNR' in df.columns:
        df['SNR'] = pd.to_numeric(df['SNR'], errors='coerce')
    if 'Resolution' in df.columns:
        df['Resolution'] = pd.to_numeric(df['Resolution'], errors='coerce')
    if 'detection_limit' in df.columns:
        df['detection_limit'] = pd.to_numeric(df['detection_limit'], errors='coerce')

    return df

def plot_instrumental_noise_vs_signal(df: pd.DataFrame, output_path: Path) -> None:
    """
    Generate the 'Instrumental Noise vs. Signal' plot.
    Visualizes SNR distribution and the calculated detection limit threshold.
    Per SC-003, this plot validates the signal-to-noise ratio against the detection floor.
    """
    plt.figure(figsize=(12, 8))

    # Determine the threshold column. T035 generates 'detection_limit'.
    threshold_col = 'detection_limit'
    signal_col = 'SNR'

    if threshold_col not in df.columns:
        raise KeyError(f"Column '{threshold_col}' not found in dataframe. "
                       "Ensure T035 (calculate_detection_limit) has run.")
    if signal_col not in df.columns:
        raise KeyError(f"Column '{signal_col}' not found in dataframe. "
                       "Ensure metadata extraction includes SNR.")

    # Filter out rows where SNR or detection limit is NaN
    valid_df = df[[signal_col, threshold_col]].dropna()

    if valid_df.empty:
        raise ValueError("No valid data points found to plot after removing NaNs.")

    # Plot 1: Distribution of SNR (Signal)
    ax1 = plt.subplot(2, 1, 1)
    sns.histplot(valid_df[signal_col], kde=True, color='skyblue', edgecolor='black', ax=ax1)
    ax1.axvline(valid_df[signal_col].mean(), color='red', linestyle='--', label=f'Mean SNR: {valid_df[signal_col].mean():.2f}')
    ax1.axvline(valid_df[signal_col].median(), color='green', linestyle='--', label=f'Median SNR: {valid_df[signal_col].median():.2f}')
    ax1.set_title('Distribution of Signal-to-Noise Ratio (SNR)')
    ax1.set_xlabel('SNR')
    ax1.set_ylabel('Frequency')
    ax1.legend()

    # Plot 2: Signal vs Detection Limit (Noise Floor)
    # This visualizes the "Instrumental Noise vs Signal" relationship.
    # We plot SNR against the calculated detection limit for each planet.
    ax2 = plt.subplot(2, 1, 2)
    
    # Scatter plot: SNR (y) vs Detection Limit (x)
    # Alternatively, if detection_limit is a threshold value (scalar) for the whole dataset,
    # we might plot a horizontal line. However, T035 suggests per-spectrum limits.
    # Let's assume detection_limit is the minimum SNR required for a robust detection.
    
    sns.scatterplot(x=threshold_col, y=signal_col, data=valid_df, ax=ax2, alpha=0.7, edgecolor='w')
    
    # Add a diagonal line where Signal = Limit (The "detectability" boundary)
    lim_range = [valid_df[[threshold_col, signal_col]].min().min(), valid_df[[threshold_col, signal_col]].max().max()]
    ax2.plot(lim_range, lim_range, 'r--', label='Signal = Detection Limit', linewidth=2)
    
    # Highlight points below the line (Undetected/Low Confidence)
    below_line = valid_df[valid_df[signal_col] < valid_df[threshold_col]]
    if not below_line.empty:
        ax2.scatter(below_line[threshold_col], below_line[signal_col], 
                    color='orange', label='Below Detection Threshold', alpha=0.7, edgecolor='w')

    ax2.set_title('Instrumental Noise vs. Signal: SNR vs. Detection Limit')
    ax2.set_xlabel('Calculated Detection Limit (SNR Threshold)')
    ax2.set_ylabel('Measured SNR')
    ax2.legend()
    ax2.grid(True, linestyle=':', alpha=0.6)

    plt.suptitle('Instrumental Noise vs. Signal Analysis', fontsize=16, fontweight='bold')
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    logging.info(f"Saved plot to {output_path}")

def main() -> None:
    """Main entry point for T036."""
    setup_logging()
    config = get_config()
    
    # Load data
    try:
        df = load_analysis_data()
    except (FileNotFoundError, KeyError, ValueError) as e:
        logging.error(f"Failed to load data for plotting: {e}")
        return

    # Define output path: results/plots/instrumental_noise_vs_signal.png
    output_dir = Path(config['paths']['results_plots'])
    output_path = output_dir / 'instrumental_noise_vs_signal.png'
    
    try:
        plot_instrumental_noise_vs_signal(df, output_path)
        logging.info("Task T036 completed successfully.")
    except Exception as e:
        logging.error(f"Failed to generate plot: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()