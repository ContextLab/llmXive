"""
Baseline CUSUM (Cumulative Sum) Anomaly Detection Script.

Implements change point detection using the CUSUM algorithm on time series data.
Outputs anomaly scores and binary flags to data/results/cusum_predictions.csv.

This script is part of User Story 2 (Baseline Comparison Engine) and integrates
with the shared data loader from T004.
"""
import os
import sys
import logging
import argparse
import json
from pathlib import Path
from typing import Tuple, Optional, Dict, Any, List

import numpy as np
import pandas as pd

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from lib.data_loader import load_processed_data
from lib.metrics import calculate_metrics
from lib.utils import set_seed

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
DEFAULT_K = 0.5  # Reference value (slack)
DEFAULT_H = 5.0  # Decision threshold
DEFAULT_DRIFT = 0.0
SEED = 42

def load_and_validate_data(data_path: Path) -> pd.DataFrame:
    """
    Load preprocessed time series data and validate structure.

    Args:
        data_path: Path to the processed CSV file.

    Returns:
        DataFrame with 'timestamp' and 'value' columns.

    Raises:
        ValueError: If required columns are missing or data is invalid.
    """
    logger.info(f"Loading data from {data_path}")
    try:
        df = pd.read_csv(data_path)
    except FileNotFoundError:
        logger.error(f"Data file not found: {data_path}")
        raise
    except Exception as e:
        logger.error(f"Error reading data file: {e}")
        raise

    required_cols = ['timestamp', 'value']
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")

    # Validate data types
    if not pd.api.types.is_numeric_dtype(df['value']):
        raise ValueError("Column 'value' must be numeric")

    # Handle missing values
    if df['value'].isna().any():
        logger.warning("Missing values detected in 'value' column. Interpolating.")
        df['value'] = df['value'].interpolate(method='linear')
        df = df.dropna(subset=['value'])

    if len(df) == 0:
        raise ValueError("No valid data points remaining after cleaning")

    logger.info(f"Loaded {len(df)} data points")
    return df

def calculate_cusum_parameters(
    data: pd.Series,
    k: float = DEFAULT_K,
    h: float = DEFAULT_H,
    drift: float = DEFAULT_DRIFT
) -> Tuple[float, float]:
    """
    Calculate CUSUM parameters based on data statistics.

    Args:
        data: Time series data.
        k: Reference value (slack).
        h: Decision threshold.
        drift: Drift term.

    Returns:
        Tuple of (k, h) used for detection.
    """
    mean_val = data.mean()
    std_val = data.std()

    if std_val == 0:
        logger.warning("Standard deviation is zero. Using default k and h.")
        return k, h

    # Normalize k and h relative to standard deviation if not provided
    # Default k is often 0.5 * sigma in standardized units
    # Default h is often 4-5 * sigma
    # Here we assume k and h are already in data units or standardized
    # If they are standardized, we need to scale them back
    # For this implementation, we assume k and h are in data units
    # If the user wants standardized, they should pass k=0.5, h=5.0
    # and we will scale them by std_val
    # However, to match common practice, let's assume k and h are in standard deviation units
    # and we scale them here.

    # Re-interpret: k and h are often given in terms of sigma.
    # Let's scale them by the standard deviation of the data.
    k_scaled = k * std_val
    h_scaled = h * std_val

    logger.info(f"Using CUSUM parameters: k={k_scaled:.4f}, h={h_scaled:.4f} (scaled by std={std_val:.4f})")
    return k_scaled, h_scaled

def run_cusum_detection(
    data: pd.Series,
    k: float,
    h: float,
    drift: float = DEFAULT_DRIFT
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Run CUSUM anomaly detection algorithm.

    Implements the one-sided CUSUM for detecting mean shifts.
    Returns positive CUSUM, negative CUSUM, and anomaly scores.

    Args:
        data: Time series data.
        k: Reference value (slack).
        h: Decision threshold.
        drift: Drift term.

    Returns:
        Tuple of (positive_cusum, negative_cusum, anomaly_scores).
        anomaly_scores are the maximum of the two CUSUMs.
    """
    n = len(data)
    positive_cusum = np.zeros(n)
    negative_cusum = np.zeros(n)
    anomaly_scores = np.zeros(n)

    # Initialize CUSUM values
    s_pos = 0.0
    s_neg = 0.0

    # Calculate the target mean (assuming the first part of the series is normal)
    # For simplicity, we use the overall mean as the target
    target_mean = data.mean()

    for i in range(n):
        x = data.iloc[i]
        diff = x - target_mean

        # Update positive CUSUM (detects upward shifts)
        s_pos = max(0, s_pos + diff - k - drift)
        positive_cusum[i] = s_pos

        # Update negative CUSUM (detects downward shifts)
        s_neg = max(0, s_neg - diff - k + drift)
        negative_cusum[i] = s_neg

        # Anomaly score is the maximum of the two CUSUMs
        anomaly_scores[i] = max(s_pos, s_neg)

    return positive_cusum, negative_cusum, anomaly_scores

def detect_anomalies(
    anomaly_scores: np.ndarray,
    threshold: Optional[float] = None
) -> np.ndarray:
    """
    Detect anomalies based on CUSUM scores.

    Args:
        anomaly_scores: CUSUM anomaly scores.
        threshold: Decision threshold. If None, uses the max score as a dynamic threshold.

    Returns:
        Binary array indicating anomalies (1) or normal (0).
    """
    if threshold is None:
        # Dynamic threshold: use a percentile or a multiple of the mean
        # Common practice: threshold = h (from CUSUM parameters)
        # Here we use a simple heuristic: 95th percentile of scores
        threshold = np.percentile(anomaly_scores, 95)
        logger.info(f"Using dynamic threshold: {threshold:.4f}")

    # Anomalies are points where the score exceeds the threshold
    # However, CUSUM scores are cumulative, so once a threshold is crossed,
    # subsequent points may also be flagged.
    # To avoid long runs of false positives, we can use a minimum distance
    # or only flag the point where the threshold is first crossed.
    # For this implementation, we flag all points above the threshold.

    is_anomaly = (anomaly_scores > threshold).astype(int)

    # Optional: Apply a minimum duration filter to remove isolated spikes
    # This is a common post-processing step for CUSUM
    min_duration = 2
    if min_duration > 1:
        is_anomaly = _apply_min_duration_filter(is_anomaly, min_duration)

    return is_anomaly

def _apply_min_duration_filter(
    is_anomaly: np.ndarray,
    min_duration: int
) -> np.ndarray:
    """
    Apply a minimum duration filter to remove short anomaly segments.

    Args:
        is_anomaly: Binary anomaly flags.
        min_duration: Minimum duration for an anomaly segment.

    Returns:
        Filtered binary anomaly flags.
    """
    filtered = is_anomaly.copy()
    n = len(is_anomaly)
    i = 0
    while i < n:
        if is_anomaly[i] == 1:
            # Find the end of this anomaly segment
            start = i
            while i < n and is_anomaly[i] == 1:
                i += 1
            end = i
            duration = end - start

            if duration < min_duration:
                # Remove this short segment
                filtered[start:end] = 0
        else:
            i += 1
    return filtered

def save_predictions(
    df: pd.DataFrame,
    anomaly_scores: np.ndarray,
    is_anomaly: np.ndarray,
    output_path: Path,
    metadata: Dict[str, Any]
) -> None:
    """
    Save predictions to a CSV file.

    Args:
        df: Original data DataFrame.
        anomaly_scores: Anomaly scores.
        is_anomaly: Binary anomaly flags.
        output_path: Path to the output CSV file.
        metadata: Metadata to include in the output.
    """
    output_df = df.copy()
    output_df['cusum_score'] = anomaly_scores
    output_df['is_anomaly'] = is_anomaly

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    output_df.to_csv(output_path, index=False)
    logger.info(f"Saved predictions to {output_path}")

    # Save metadata as JSON
    metadata_path = output_path.with_suffix('.json')
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"Saved metadata to {metadata_path}")

def print_summary(
    is_anomaly: np.ndarray,
    anomaly_scores: np.ndarray,
    threshold: float
) -> None:
    """
    Print a summary of the detection results.

    Args:
        is_anomaly: Binary anomaly flags.
        anomaly_scores: Anomaly scores.
        threshold: Decision threshold used.
    """
    n_total = len(is_anomaly)
    n_anomalies = np.sum(is_anomaly)
    anomaly_rate = n_anomalies / n_total

    logger.info("=== CUSUM Detection Summary ===")
    logger.info(f"Total points: {n_total}")
    logger.info(f"Detected anomalies: {n_anomalies} ({anomaly_rate:.2%})")
    logger.info(f"Threshold used: {threshold:.4f}")
    logger.info(f"Score range: [{anomaly_scores.min():.4f}, {anomaly_scores.max():.4f}]")
    logger.info(f"Mean score: {anomaly_scores.mean():.4f}")
    logger.info("==============================")

def main() -> None:
    """
    Main entry point for the CUSUM baseline script.
    """
    parser = argparse.ArgumentParser(description='CUSUM Anomaly Detection')
    parser.add_argument(
        '--input',
        type=str,
        default='data/processed/series_with_anomalies.csv',
        help='Path to the input data file'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='data/results/cusum_predictions.csv',
        help='Path to the output predictions file'
    )
    parser.add_argument(
        '--k',
        type=float,
        default=DEFAULT_K,
        help='Reference value (slack)'
    )
    parser.add_argument(
        '--h',
        type=float,
        default=DEFAULT_H,
        help='Decision threshold'
    )
    parser.add_argument(
        '--drift',
        type=float,
        default=DEFAULT_DRIFT,
        help='Drift term'
    )
    parser.add_argument(
        '--seed',
        type=int,
        default=SEED,
        help='Random seed for reproducibility'
    )

    args = parser.parse_args()

    # Set seed for reproducibility
    set_seed(args.seed)

    # Paths
    input_path = Path(args.input)
    output_path = Path(args.output)

    # Load and validate data
    try:
        df = load_and_validate_data(input_path)
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        sys.exit(1)

    # Calculate CUSUM parameters
    k, h = calculate_cusum_parameters(
        df['value'],
        k=args.k,
        h=args.h,
        drift=args.drift
    )

    # Run CUSUM detection
    try:
        _, _, anomaly_scores = run_cusum_detection(
            df['value'],
            k=k,
            h=h,
            drift=args.drift
        )
    except Exception as e:
        logger.error(f"Failed to run CUSUM detection: {e}")
        sys.exit(1)

    # Detect anomalies
    try:
        is_anomaly = detect_anomalies(anomaly_scores)
    except Exception as e:
        logger.error(f"Failed to detect anomalies: {e}")
        sys.exit(1)

    # Prepare metadata
    metadata = {
        'algorithm': 'CUSUM',
        'k': k,
        'h': h,
        'drift': args.drift,
        'threshold': np.percentile(anomaly_scores, 95),
        'seed': args.seed,
        'n_points': len(df),
        'n_anomalies': int(np.sum(is_anomaly)),
        'anomaly_rate': float(np.sum(is_anomaly) / len(df))
    }

    # Save predictions
    try:
        save_predictions(df, anomaly_scores, is_anomaly, output_path, metadata)
    except Exception as e:
        logger.error(f"Failed to save predictions: {e}")
        sys.exit(1)

    # Print summary
    print_summary(is_anomaly, anomaly_scores, metadata['threshold'])

    logger.info("CUSUM detection completed successfully")

if __name__ == '__main__':
    main()