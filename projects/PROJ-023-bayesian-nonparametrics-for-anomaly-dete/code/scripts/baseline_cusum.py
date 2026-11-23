"""
Cumulative Sum (CUSUM) Baseline for Anomaly Detection.

This script implements the CUSUM algorithm for change point detection in time series data.
It reads the unified data format from T004 and outputs predictions to a CSV file.
The implementation follows FR-003 and uses the shared loader infrastructure.

Author: llmXive Research Agent
"""

import os
import sys
import logging
import argparse
import json
import time
from pathlib import Path
from typing import Tuple, List, Dict, Any, Optional

import numpy as np
import pandas as pd

# Importing from local lib modules
try:
    from lib.utils import set_seed, normalize_data
    from lib.metrics import calculate_metrics
except ImportError:
    print("Error: Required modules in code/lib/ not found.")
    sys.exit(1)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

def load_and_validate_data(data_path: str) -> Tuple[np.ndarray, np.ndarray]:
    """
    Load and validate input time series data.

    Args:
        data_path (str): Path to the input CSV.

    Returns:
        Tuple[np.ndarray, np.ndarray]: (timestamps, values)
    """
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Data file not found: {data_path}")

    df = pd.read_csv(data_path)
    if 'timestamp' not in df.columns or 'value' not in df.columns:
        raise ValueError("Invalid CSV format. Expected 'timestamp' and 'value' columns.")

    timestamps = df['timestamp'].values.astype(float)
    values = df['value'].values.astype(float)

    # Basic validation for missing values
    if np.any(np.isnan(values)):
        logger.warning("NaN values detected. Interpolating...")
        values = pd.Series(values).interpolate().values
        # Handle any remaining NaNs at edges
        values = pd.Series(values).fillna(method='bfill').fillna(method='ffill').values

    if len(values) == 0:
        raise ValueError("Data is empty after validation.")

    return timestamps, values

def calculate_cusum_parameters(values: np.ndarray) -> Tuple[float, float]:
    """
    Calculate CUSUM parameters (mean and standard deviation).

    Args:
        values (np.ndarray): Input values.

    Returns:
        Tuple[float, float]: (mean, std)
    """
    mean = np.mean(values)
    std = np.std(values)
    if std == 0 or np.isnan(std):
        std = 1e-6
    return mean, std

def run_cusum_detection(
    values: np.ndarray,
    threshold: float,
    drift: float = 0.5
) -> np.ndarray:
    """
    Run CUSUM detection algorithm.

    Implements the standard CUSUM procedure:
    S_i = max(0, S_{i-1} + (x_i - mu)/sigma - k)
    where k is the drift parameter.

    Args:
        values (np.ndarray): Input values.
        threshold (float): Detection threshold (H).
        drift (float): Drift parameter (k).

    Returns:
        np.ndarray: Anomaly flags (0 or 1).
    """
    mean, std = calculate_cusum_parameters(values)
    # Normalize to z-scores
    normalized = (values - mean) / std

    cusum_pos = np.zeros(len(values))
    cusum_neg = np.zeros(len(values))
    anomalies = np.zeros(len(values), dtype=int)

    # CUSUM state
    for i in range(1, len(values)):
        # Update positive CUSUM (detects upward shifts)
        cusum_pos[i] = max(0.0, cusum_pos[i-1] + normalized[i] - drift)
        # Update negative CUSUM (detects downward shifts)
        cusum_neg[i] = max(0.0, cusum_neg[i-1] - normalized[i] - drift)

        # Flag anomaly if either exceeds threshold
        if cusum_pos[i] > threshold or cusum_neg[i] > threshold:
            anomalies[i] = 1

    return anomalies

def detect_anomalies(values: np.ndarray, threshold: float) -> np.ndarray:
    """
    Detect anomalies using CUSUM.

    Args:
        values (np.ndarray): Input values.
        threshold (float): Detection threshold.

    Returns:
        np.ndarray: Anomaly flags.
    """
    return run_cusum_detection(values, threshold)

def save_predictions(
    timestamps: np.ndarray,
    anomalies: np.ndarray,
    output_path: str
) -> None:
    """
    Save predictions to CSV.

    Args:
        timestamps (np.ndarray): Input timestamps.
        anomalies (np.ndarray): Anomaly flags.
        output_path (str): Output CSV path.
    """
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    df = pd.DataFrame({
        'timestamp': timestamps,
        'anomaly_flag': anomalies
    })
    df.to_csv(output_path, index=False)
    logger.info(f"Predictions saved to {output_path}")

def print_summary(anomalies: np.ndarray) -> None:
    """Print summary statistics."""
    total = len(anomalies)
    detected = np.sum(anomalies)
    rate = 100 * detected / total if total > 0 else 0.0
    logger.info(f"Total points: {total}, Anomalies detected: {detected} ({rate:.2f}%)")

def load_threshold_config(config_path: str) -> float:
    """
    Load threshold configuration.

    Expects a YAML file with a 'value' key for the threshold.
    Falls back to default if missing or invalid, but logs a warning.

    Args:
        config_path (str): Path to config YAML.

    Returns:
        float: Threshold value.
    """
    import yaml
    default = 5.0
    
    if not os.path.exists(config_path):
        logger.warning(f"Config not found: {config_path}. Using default threshold {default}.")
        return default

    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        if not config or 'value' not in config:
            logger.warning(f"Config missing 'value' key. Using default threshold {default}.")
            return default
        
        val = float(config['value'])
        if val <= 0:
            logger.warning(f"Threshold value {val} is non-positive. Using default {default}.")
            return default
        
        return val
    except Exception as e:
        logger.warning(f"Error loading config: {e}. Using default threshold {default}.")
        return default

def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="CUSUM Anomaly Detection")
    parser.add_argument('--data', type=str, required=True, help='Input data CSV')
    parser.add_argument('--output', type=str, default='data/results/cusum_predictions.csv', help='Output CSV')
    parser.add_argument('--config', type=str, default='code/config/threshold_strategy.yaml', help='Threshold config')
    args = parser.parse_args()

    # Ensure reproducibility
    set_seed(42)

    start_time = time.time()
    
    try:
        timestamps, values = load_and_validate_data(args.data)
        threshold = load_threshold_config(args.config)

        logger.info(f"Running CUSUM detection with threshold={threshold}")
        anomalies = detect_anomalies(values, threshold)
        
        save_predictions(timestamps, anomalies, args.output)
        print_summary(anomalies)
        
        elapsed = time.time() - start_time
        logger.info(f"CUSUM detection completed in {elapsed:.2f} seconds.")
        
    except FileNotFoundError as e:
        logger.error(f"Data loading failed: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Data validation failed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()