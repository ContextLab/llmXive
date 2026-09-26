"""
Script to Render Figure 1: Time Series with Injected Anomalies and Detection Scores.

This script loads the processed time series data with injected anomalies and
the anomaly scores from the Bayesian GP model. It generates a plot showing
the time series, the injected anomalies, and the detection scores.

Author: Research Team
Date: 2026-04-29
"""

import os
import sys
import logging
import argparse
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_and_align_data(
    series_path: Path,
    predictions_path: Path
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load and align the time series and prediction data.

    Args:
        series_path (Path): Path to the series with anomalies CSV.
        predictions_path (Path): Path to the predictions CSV.

    Returns:
        Tuple[pd.DataFrame, pd.DataFrame]: The aligned DataFrames.

    Raises:
        FileNotFoundError: If input files do not exist.
        ValueError: If data lengths mismatch significantly or required columns missing.
    """
    if not series_path.exists():
        raise FileNotFoundError(f"Series file not found: {series_path}")
    if not predictions_path.exists():
        raise FileNotFoundError(f"Predictions file not found: {predictions_path}")

    df_series = pd.read_csv(series_path)
    df_pred = pd.read_csv(predictions_path)

    # Validate required columns
    required_series_cols = ['timestamp', 'value']
    required_pred_cols = ['timestamp', 'anomaly_score']

    for col in required_series_cols:
        if col not in df_series.columns:
            raise ValueError(f"Series file missing required column: {col}")
    
    for col in required_pred_cols:
        if col not in df_pred.columns:
            raise ValueError(f"Prediction file missing required column: {col}")

    # Ensure they have the same length
    if len(df_series) != len(df_pred):
        logger.warning(
            f"Length mismatch: Series ({len(df_series)}) vs Predictions ({len(df_pred)}). "
            "Truncating to minimum length."
        )
        min_len = min(len(df_series), len(df_pred))
        df_series = df_series.iloc[:min_len].reset_index(drop=True)
        df_pred = df_pred.iloc[:min_len].reset_index(drop=True)

    # Sort by timestamp to ensure alignment if not already sorted
    if 'timestamp' in df_series.columns:
        df_series = df_series.sort_values('timestamp').reset_index(drop=True)
        df_pred = df_pred.sort_values('timestamp').reset_index(drop=True)

    logger.info(f"Loaded and aligned {len(df_series)} rows")
    return df_series, df_pred


def plot_timeseries_with_anomalies(
    df_series: pd.DataFrame,
    df_pred: pd.DataFrame,
    output_path: Path,
    title: str = "Time Series with Injected Anomalies and Detection Scores"
) -> None:
    """
    Plot the time series with injected anomalies and detection scores.

    Args:
        df_series (pd.DataFrame): The time series data with anomalies.
        df_pred (pd.DataFrame): The prediction data with anomaly scores.
        output_path (Path): Path to save the figure.
        title (str): Title of the plot.
    """
    # Set style
    sns.set(style="whitegrid")
    fig, ax1 = plt.subplots(figsize=(14, 7))

    # Plot time series
    ax1.plot(
        df_series['timestamp'], 
        df_series['value'], 
        label='Time Series', 
        color='blue', 
        alpha=0.7,
        linewidth=1.5
    )

    # Highlight anomalies
    if 'is_anomaly' in df_series.columns:
        anomaly_mask = df_series['is_anomaly'] == 1
        if anomaly_mask.any():
            # Scatter plot for anomalies
            ax1.scatter(
                df_series.loc[anomaly_mask, 'timestamp'],
                df_series.loc[anomaly_mask, 'value'],
                color='red', 
                label='Injected Anomalies', 
                s=60, 
                zorder=5,
                marker='x',
                edgecolors='darkred'
            )

    ax1.set_xlabel('Time', fontsize=12)
    ax1.set_ylabel('Value', fontsize=12)
    ax1.set_title(title, fontsize=14, fontweight='bold')
    ax1.legend(loc='upper left')

    # Add secondary axis for anomaly scores
    if 'anomaly_score' in df_pred.columns:
        ax2 = ax1.twinx()
        ax2.plot(
            df_pred['timestamp'], 
            df_pred['anomaly_score'],
            label='Anomaly Score', 
            color='orange', 
            linestyle='--', 
            alpha=0.8,
            linewidth=1.5
        )
        ax2.set_ylabel('Anomaly Score', fontsize=12)
        # Combine legends
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')

    plt.tight_layout()

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save figure
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    logger.info(f"Saved figure to {output_path}")


def main() -> None:
    """
    Main entry point for the Figure 1 rendering script.
    """
    parser = argparse.ArgumentParser(description="Render Figure 1: Time Series with Anomalies")
    parser.add_argument(
        "--series",
        type=str,
        default="data/processed/series_with_anomalies.csv",
        help="Path to series with anomalies CSV"
    )
    parser.add_argument(
        "--predictions",
        type=str,
        default="data/results/bayesian_predictions.csv",
        help="Path to predictions CSV"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="paper/figures/fig1_timeseries.png",
        help="Path to save the figure"
    )
    parser.add_argument(
        "--title",
        type=str,
        default="Time Series with Injected Anomalies and Detection Scores",
        help="Title of the plot"
    )
    args = parser.parse_args()

    series_path = Path(args.series)
    predictions_path = Path(args.predictions)
    output_path = Path(args.output)

    try:
        # Load and align data
        df_series, df_pred = load_and_align_data(series_path, predictions_path)

        # Plot
        plot_timeseries_with_anomalies(
            df_series, df_pred, output_path, title=args.title
        )

        logger.info("Figure 1 rendering completed successfully.")

    except FileNotFoundError as e:
        logger.error(f"Input file missing: {e}")
        logger.error("Ensure T004 (data download) and T016 (bayesian inference) have run successfully.")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Data validation error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to render Figure 1: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()