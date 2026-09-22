"""
CUSUM (Cumulative Sum) Baseline for Anomaly Detection.

Implements the CUSUM algorithm for change point detection in time series.
Outputs anomaly scores and binary flags to data/results/cusum_predictions.csv.
"""
import os
import sys
import logging
import argparse
from pathlib import Path
from typing import Tuple, Optional, Dict, Any
import numpy as np
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project root path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DATA_PATH = PROJECT_ROOT / "data" / "processed" / "series_with_anomalies.csv"
GROUND_TRUTH_PATH = PROJECT_ROOT / "data" / "processed" / "ground_truth.csv"
OUTPUT_PATH = PROJECT_ROOT / "data" / "results" / "cusum_predictions.csv"

def load_and_validate_data(data_path: Path = None) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load the preprocessed time series and ground truth data.

    Args:
        data_path: Path to the processed time series CSV. Defaults to project standard.

    Returns:
        Tuple of (time_series_df, ground_truth_df)
    """
    if data_path is None:
        data_path = PROCESSED_DATA_PATH

    if not data_path.exists():
        raise FileNotFoundError(
            f"Processed data not found at {data_path}. "
            "Please run inject_anomalies.py first."
        )

    logger.info(f"Loading data from {data_path}")
    df = pd.read_csv(data_path)

    # Validate required columns
    required_cols = ['timestamp', 'value']
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")

    # Handle missing values via interpolation
    df['value'] = df['value'].interpolate(method='linear')
    df['value'] = df['value'].fillna(method='bfill').fillna(method='ffill')

    logger.info(f"Loaded {len(df)} data points")
    return df

def calculate_cusum_parameters(series: np.ndarray) -> Tuple[float, float, float]:
    """
    Calculate CUSUM parameters based on the data statistics.

    Uses a standard approach:
    - Threshold (h): 5.0 * sigma (adjustable)
    - Drift (k): 0.5 * sigma (adjustable)

    Args:
        series: The time series values as a numpy array.

    Returns:
        Tuple of (mean, std, sigma)
    """
    mean_val = np.mean(series)
    std_val = np.std(series)
    sigma = std_val
    return mean_val, std_val, sigma

def run_cusum_detection(
    series: np.ndarray,
    threshold: float = 5.0,
    drift: float = 0.5,
    sigma: float = 1.0
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Run the CUSUM algorithm to detect anomalies.

    The CUSUM statistic is updated as:
    S_t = max(0, S_{t-1} + (x_t - mean) - drift)

    An anomaly is flagged if S_t > threshold * sigma.

    Args:
        series: Time series values.
        threshold: Multiplier for sigma to determine the detection threshold.
        drift: Drift parameter (k) in the CUSUM update.
        sigma: Standard deviation of the series.

    Returns:
        Tuple of (scores, binary_flags, cusum_statistics)
    """
    mean_val = np.mean(series)
    n = len(series)

    # Initialize arrays
    cusum_stats = np.zeros(n)
    scores = np.zeros(n)
    binary_flags = np.zeros(n, dtype=int)

    # Detection threshold in absolute units
    detection_threshold = threshold * sigma

    # Run CUSUM
    for t in range(1, n):
        # Update CUSUM statistic
        # One-sided CUSUM for upward shifts
        cusum_stats[t] = max(0, cusum_stats[t-1] + (series[t] - mean_val) - (drift * sigma))
        
        # Calculate anomaly score (normalized CUSUM value)
        scores[t] = cusum_stats[t] / sigma if sigma > 0 else 0.0

        # Flag anomaly if threshold exceeded
        if cusum_stats[t] > detection_threshold:
            binary_flags[t] = 1
        
        # Reset CUSUM if it drops significantly to avoid accumulation of old anomalies
        # (Optional: can be tuned, here we keep standard implementation)

    # Handle the first point (no history)
    scores[0] = 0.0
    binary_flags[0] = 0

    logger.info(f"CUSUM detection complete. Found {np.sum(binary_flags)} anomalies.")
    return scores, binary_flags, cusum_stats

def save_predictions(
    df: pd.DataFrame,
    scores: np.ndarray,
    binary_flags: np.ndarray,
    output_path: Path = None
) -> None:
    """
    Save the predictions to a CSV file.

    Args:
        df: Original dataframe with timestamp and value.
        scores: Anomaly scores.
        binary_flags: Binary anomaly flags.
        output_path: Path to save the CSV.
    """
    if output_path is None:
        output_path = OUTPUT_PATH

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Create result dataframe
    result_df = pd.DataFrame({
        'timestamp': df['timestamp'],
        'value': df['value'],
        'cusum_score': scores,
        'is_anomaly': binary_flags
    })

    # Save to CSV
    result_df.to_csv(output_path, index=False)
    logger.info(f"Saved predictions to {output_path}")

def print_summary(df: pd.DataFrame, scores: np.ndarray, binary_flags: np.ndarray) -> None:
    """
    Print a summary of the CUSUM detection results.

    Args:
        df: Original dataframe.
        scores: Anomaly scores.
        binary_flags: Binary anomaly flags.
    """
    total_points = len(df)
    anomaly_count = int(np.sum(binary_flags))
    anomaly_rate = (anomaly_count / total_points) * 100 if total_points > 0 else 0

    logger.info("=" * 50)
    logger.info("CUSUM Detection Summary")
    logger.info("=" * 50)
    logger.info(f"Total data points: {total_points}")
    logger.info(f"Anomalies detected: {anomaly_count} ({anomaly_rate:.2f}%)")
    logger.info(f"Mean CUSUM score: {np.mean(scores):.4f}")
    logger.info(f"Max CUSUM score: {np.max(scores):.4f}")
    logger.info("=" * 50)

def main():
    """
    Main entry point for the CUSUM baseline script.
    """
    parser = argparse.ArgumentParser(description="Run CUSUM anomaly detection baseline.")
    parser.add_argument(
        "--data-path",
        type=str,
        default=None,
        help="Path to the processed time series CSV (default: data/processed/series_with_anomalies.csv)"
    )
    parser.add_argument(
        "--output-path",
        type=str,
        default=None,
        help="Path to save predictions CSV (default: data/results/cusum_predictions.csv)"
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=5.0,
        help="CUSUM threshold multiplier (default: 5.0)"
    )
    parser.add_argument(
        "--drift",
        type=float,
        default=0.5,
        help="CUSUM drift parameter (default: 0.5)"
    )
    args = parser.parse_args()

    try:
        # Load data
        df = load_and_validate_data(
            Path(args.data_path) if args.data_path else None
        )

        # Extract series
        series = df['value'].values

        # Calculate parameters
        mean_val, std_val, sigma = calculate_cusum_parameters(series)
        logger.info(f"Data statistics: mean={mean_val:.4f}, std={std_val:.4f}")

        # Run CUSUM detection
        scores, binary_flags, _ = run_cusum_detection(
            series,
            threshold=args.threshold,
            drift=args.drift,
            sigma=sigma
        )

        # Save predictions
        save_predictions(
            df,
            scores,
            binary_flags,
            Path(args.output_path) if args.output_path else None
        )

        # Print summary
        print_summary(df, scores, binary_flags)

        logger.info("CUSUM baseline completed successfully.")

    except Exception as e:
        logger.error(f"Error running CUSUM baseline: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()