"""
Baseline CUSUM (Cumulative Sum) Anomaly Detection Script.

This script implements the CUSUM algorithm for change point detection
in time series data. It outputs predictions in a CSV format compatible
with the evaluation pipeline.

Author: Research Team
Date: 2026-04-29
"""

import os
import sys
import logging
import argparse
from pathlib import Path
from typing import Tuple, Optional, Dict, Any

import numpy as np
import pandas as pd

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_and_validate_data(input_path: Path) -> pd.DataFrame:
    """
    Load and validate the input time series data.

    Args:
        input_path (Path): Path to the input CSV file.

    Returns:
        pd.DataFrame: The loaded and validated DataFrame.
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    df = pd.read_csv(input_path)

    required_columns = ['timestamp', 'value']
    if not all(col in df.columns for col in required_columns):
        raise ValueError(f"Input data must contain columns: {required_columns}")

    # Handle missing values
    df['value'] = df['value'].interpolate(method='linear')
    df['value'] = df['value'].fillna(method='bfill').fillna(method='ffill')

    logger.info(f"Loaded data from {input_path}: {len(df)} rows")
    return df


def calculate_cusum_parameters(data: np.ndarray) -> Tuple[float, float]:
    """
    Calculate the mean and standard deviation for CUSUM thresholding.

    Args:
        data (np.ndarray): The time series data.

    Returns:
        Tuple[float, float]: (mean, std_dev)
    """
    mean_val = np.mean(data)
    std_dev = np.std(data)
    logger.info(f"Calculated parameters: mean={mean_val:.4f}, std_dev={std_dev:.4f}")
    return mean_val, std_dev


def run_cusum_detection(
    data: np.ndarray,
    mean_val: float,
    std_dev: float,
    threshold: float = 5.0,
    slack: float = 0.5
) -> np.ndarray:
    """
    Run CUSUM anomaly detection.

    Args:
        data (np.ndarray): The time series data.
        mean_val (float): Mean of the data.
        std_dev (float): Standard deviation of the data.
        threshold (float): Threshold for anomaly detection.
        slack (float): Slack parameter to reduce sensitivity.

    Returns:
        np.ndarray: Binary anomaly flags (1 = anomaly, 0 = normal).
    """
    n = len(data)
    anomalies = np.zeros(n, dtype=int)

    # Standardize data
    z_scores = (data - mean_val) / (std_dev + 1e-8)

    # Initialize CUSUM statistics
    S_pos = np.zeros(n)
    S_neg = np.zeros(n)

    for i in range(1, n):
        S_pos[i] = max(0, S_pos[i-1] + z_scores[i] - slack)
        S_neg[i] = max(0, S_neg[i-1] - z_scores[i] - slack)

        if S_pos[i] > threshold or S_neg[i] > threshold:
            anomalies[i] = 1

    # Apply a simple smoothing to reduce noise (optional)
    # An anomaly is confirmed if it persists for at least 2 steps
    smoothed = np.zeros(n, dtype=int)
    for i in range(1, n-1):
        if anomalies[i] and (anomalies[i-1] or anomalies[i+1]):
            smoothed[i] = 1
        elif anomalies[i] and i == n-1 and anomalies[i-1]:
            smoothed[i] = 1

    logger.info(f"Detected {smoothed.sum()} anomalies using CUSUM")
    return smoothed


def save_predictions(
    df: pd.DataFrame,
    predictions: np.ndarray,
    output_path: Path
) -> None:
    """
    Save predictions to a CSV file.

    Args:
        df (pd.DataFrame): The original DataFrame with timestamps.
        predictions (np.ndarray): Binary anomaly flags.
        output_path (Path): Path to save the output CSV.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    result_df = df.copy()
    result_df['is_anomaly'] = predictions
    result_df.to_csv(output_path, index=False)

    logger.info(f"Saved predictions to {output_path}")


def print_summary(predictions: np.ndarray) -> None:
    """
    Print a summary of the detection results.

    Args:
        predictions (np.ndarray): Binary anomaly flags.
    """
    total = len(predictions)
    anomalies = predictions.sum()
    rate = anomalies / total * 100

    logger.info("Detection Summary:")
    logger.info(f"  Total points: {total}")
    logger.info(f"  Anomalies detected: {anomalies}")
    logger.info(f"  Anomaly rate: {rate:.2f}%")


def main() -> None:
    """
    Main entry point for the CUSUM baseline script.
    """
    parser = argparse.ArgumentParser(description="CUSUM Anomaly Detection")
    parser.add_argument(
        "--input",
        type=str,
        default="data/processed/series_with_anomalies.csv",
        help="Path to input CSV file"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/results/cusum_predictions.csv",
        help="Path to output CSV file"
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=5.0,
        help="CUSUM threshold"
    )
    parser.add_argument(
        "--slack",
        type=float,
        default=0.5,
        help="CUSUM slack parameter"
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    try:
        # Load data
        df = load_and_validate_data(input_path)
        data = df['value'].values

        # Calculate parameters
        mean_val, std_dev = calculate_cusum_parameters(data)

        # Run detection
        predictions = run_cusum_detection(
            data, mean_val, std_dev,
            threshold=args.threshold, slack=args.slack
        )

        # Save results
        save_predictions(df, predictions, output_path)

        # Print summary
        print_summary(predictions)

    except Exception as e:
        logger.error(f"CUSUM detection failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
