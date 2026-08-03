"""
render_fig1.py

Implements Task T028: Plot time series with injected anomalies and detection scores.
Saves the figure to paper/figures/fig1_timeseries.png.

Dependencies:
- matplotlib, seaborn (from requirements.txt)
- pandas, numpy (from requirements.txt)
- code/lib/utils.py (ensure_output_dir, set_seed)
"""

import os
import sys
import logging
import argparse
from pathlib import Path
from typing import Optional, Dict, Any

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Add project root to path to allow relative imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from lib.utils import ensure_output_dir, set_seed

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
FIG_WIDTH = 12
FIG_HEIGHT = 6
DPI = 300
ANOMALY_COLOR = '#d62728'  # Red for anomalies
NORMAL_COLOR = '#1f77b4'   # Blue for normal
SCORE_COLOR = '#2ca02c'    # Green for detection scores
BACKGROUND_COLOR = '#f5f5f5'

def load_and_align_data(
    series_path: Path,
    ground_truth_path: Path,
    predictions_path: Path
) -> pd.DataFrame:
    """
    Load time series, ground truth, and predictions, then align them.

    Args:
        series_path: Path to data/processed/series_with_anomalies.csv
        ground_truth_path: Path to data/processed/ground_truth.csv
        predictions_path: Path to data/results/bayesian_predictions.csv

    Returns:
        Aligned DataFrame with columns: 'time', 'value', 'is_anomaly', 'score'
    """
    logger.info(f"Loading series data from {series_path}")
    series_df = pd.read_csv(series_path)

    logger.info(f"Loading ground truth from {ground_truth_path}")
    gt_df = pd.read_csv(ground_truth_path)

    logger.info(f"Loading predictions from {predictions_path}")
    pred_df = pd.read_csv(predictions_path)

    # Ensure 'time' column exists and is consistent
    if 'time' not in series_df.columns:
        raise ValueError("Series data must contain a 'time' column")
    if 'time' not in gt_df.columns:
        raise ValueError("Ground truth must contain a 'time' column")
    if 'time' not in pred_df.columns:
        raise ValueError("Predictions must contain a 'time' column")

    # Merge ground truth
    merged = series_df.merge(
        gt_df[['time', 'is_anomaly']],
        on='time',
        how='left'
    )

    # Merge predictions (anomaly score)
    # Assuming the score column is named 'score' or similar in the predictions
    score_col = None
    possible_score_cols = ['score', 'anomaly_score', 'probability', 'p_anomaly']
    for col in possible_score_cols:
        if col in pred_df.columns:
            score_col = col
            break

    if score_col is None:
        # Fallback: use the first numeric column that isn't 'time'
        numeric_cols = pred_df.select_dtypes(include=[np.number]).columns
        numeric_cols = [c for c in numeric_cols if c != 'time']
        if numeric_cols:
            score_col = numeric_cols[0]
            logger.warning(f"Using '{score_col}' as the anomaly score column.")
        else:
            raise ValueError("Predictions file must contain a numeric score column.")

    merged = merged.merge(
        pred_df[['time', score_col]],
        on='time',
        how='left',
        suffixes=('', '_pred')
    )
    merged = merged.rename(columns={score_col: 'score'})

    # Handle missing values in score (if any)
    merged['score'] = merged['score'].fillna(0)

    # Ensure 'is_anomaly' is numeric (0 or 1)
    if merged['is_anomaly'].dtype == 'object':
        merged['is_anomaly'] = merged['is_anomaly'].map({True: 1, False: 0, 1: 1, 0: 0})
    merged['is_anomaly'] = merged['is_anomaly'].fillna(0).astype(int)

    return merged

def plot_timeseries_with_anomalies(
    df: pd.DataFrame,
    output_path: Path,
    title: str = "Time Series with Injected Anomalies and Detection Scores",
    figsize: tuple = (FIG_WIDTH, FIG_HEIGHT),
    dpi: int = DPI
) -> None:
    """
    Create a plot showing the time series, injected anomalies, and detection scores.

    Args:
        df: Aligned DataFrame with 'time', 'value', 'is_anomaly', 'score'
        output_path: Path to save the figure
        title: Plot title
        figsize: Figure size (width, height)
        dpi: Resolution
    """
    logger.info(f"Generating figure: {output_path}")

    # Set style
    sns.set_theme(style="whitegrid", context="talk")
    plt.rcParams['figure.facecolor'] = 'white'
    plt.rcParams['axes.facecolor'] = BACKGROUND_COLOR
    plt.rcParams['axes.edgecolor'] = 'black'

    fig, ax1 = plt.subplots(figsize=figsize, dpi=dpi)

    # Plot time series
    ax1.plot(
        df['time'],
        df['value'],
        color=NORMAL_COLOR,
        linewidth=1.5,
        label='Time Series Value',
        alpha=0.7
    )

    # Highlight anomalies
    anomaly_mask = df['is_anomaly'] == 1
    if anomaly_mask.any():
        ax1.scatter(
            df.loc[anomaly_mask, 'time'],
            df.loc[anomaly_mask, 'value'],
            color=ANOMALY_COLOR,
            s=50,
            zorder=5,
            label='Injected Anomaly',
            edgecolors='black',
            linewidths=0.5
        )

    # Create secondary axis for anomaly scores
    ax2 = ax1.twinx()
    ax2.plot(
        df['time'],
        df['score'],
        color=SCORE_COLOR,
        linewidth=1.5,
        linestyle='--',
        label='Anomaly Score (Bayesian GP)',
        alpha=0.8
    )

    # Add threshold line if possible (optional enhancement)
    # Assuming a fixed threshold might be around 0.5 or derived from data
    # For now, just label the score axis
    ax2.set_ylabel('Anomaly Score', fontsize=12, color=SCORE_COLOR)
    ax2.tick_params(axis='y', labelcolor=SCORE_COLOR)

    # Set labels and title
    ax1.set_xlabel('Time Step', fontsize=12)
    ax1.set_ylabel('Value', fontsize=12, color=NORMAL_COLOR)
    ax1.tick_params(axis='y', labelcolor=NORMAL_COLOR)
    ax1.set_title(title, fontsize=14, fontweight='bold')

    # Combine legends
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper right')

    # Improve layout
    plt.tight_layout()

    # Ensure output directory exists
    ensure_output_dir(output_path.parent)

    # Save figure
    plt.savefig(output_path, dpi=dpi, bbox_inches='tight', facecolor='white')
    plt.close(fig)

    logger.info(f"Figure saved successfully to {output_path}")

def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Render Figure 1: Time series with anomalies and detection scores."
    )
    parser.add_argument(
        "--series",
        type=str,
        default="data/processed/series_with_anomalies.csv",
        help="Path to the time series with injected anomalies."
    )
    parser.add_argument(
        "--ground-truth",
        type=str,
        default="data/processed/ground_truth.csv",
        help="Path to the ground truth file."
    )
    parser.add_argument(
        "--predictions",
        type=str,
        default="data/results/bayesian_predictions.csv",
        help="Path to the Bayesian GP predictions file."
    )
    parser.add_argument(
        "--output",
        type=str,
        default="paper/figures/fig1_timeseries.png",
        help="Path to save the output figure."
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility."
    )

    args = parser.parse_args()

    # Set seed for reproducibility
    set_seed(args.seed)

    # Convert paths
    series_path = Path(args.series)
    ground_truth_path = Path(args.ground_truth)
    predictions_path = Path(args.predictions)
    output_path = Path(args.output)

    # Validate input files exist
    if not series_path.exists():
        logger.error(f"Series file not found: {series_path}")
        sys.exit(1)
    if not ground_truth_path.exists():
        logger.error(f"Ground truth file not found: {ground_truth_path}")
        sys.exit(1)
    if not predictions_path.exists():
        logger.error(f"Predictions file not found: {predictions_path}")
        sys.exit(1)

    try:
        # Load and align data
        df = load_and_align_data(series_path, ground_truth_path, predictions_path)

        # Generate plot
        plot_timeseries_with_anomalies(df, output_path)

        logger.info("Task T028 completed successfully.")

    except Exception as e:
        logger.error(f"Failed to generate figure: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()