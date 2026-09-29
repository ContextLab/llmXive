"""
Cumulative Sum (CUSUM) Baseline for Anomaly Detection.

This script implements the CUSUM algorithm for change point detection in time series data.
It reads the unified data format from T004 and outputs predictions to a CSV file.

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

    # Basic validation
    if np.any(np.isnan(values)):
        logger.warning("NaN values detected. Interpolating...")
        values = pd.Series(values).interpolate().values

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
    if std == 0:
        std = 1e-6
    return mean, std

def run_cusum_detection(
    values: np.ndarray,
    threshold: float,
    drift: float = 0.5
) -> np.ndarray:
    """
    Run CUSUM detection algorithm.

    Args:
        values (np.ndarray): Input values.
        threshold (float): Detection threshold.
        drift (float): Drift parameter.

    Returns:
        np.ndarray: Anomaly flags (0 or 1).
    """
    mean, std = calculate_cusum_parameters(values)
    normalized = (values - mean) / std

    cusum_pos = np.zeros(len(values))
    cusum_neg = np.zeros(len(values))
    anomalies = np.zeros(len(values), dtype=int)

    for i in range(1, len(values)):
        cusum_pos[i] = max(0, cusum_pos[i-1] + normalized[i] - drift)
        cusum_neg[i] = max(0, cusum_neg[i-1] - normalized[i] - drift)

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
    df = pd.DataFrame({
        'timestamp': timestamps,
        'anomaly_flag': anomalies
    })
    df.to_csv(output_path, index=False)
    logger.info(f"Predict saved to {output_path}")

def print_summary(anomalies: np.ndarray) -> None:
    """Print summary statistics."""
    total = len(anomalies)
    detected = np.sum(anomalies)
    logger.info(f"Total points: {total}, Anomalies detected: {detected} ({100*detected/total:.2f}%)")

def load_threshold_config(config_path: str) -> float:
    """
    Load threshold configuration.

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

    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    if config and 'value' in config:
        return float(config['value'])
    return default

def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="CUSUM Anomaly Detection")
    parser.add_argument('--data', type=str, required=True, help='Input data CSV')
    parser.add_argument('--output', type=str, default='data/results/cusum_predictions.csv', help='Output CSV')
    parser.add_argument('--config', type=str, default='code/config/threshold_strategy.yaml', help='Threshold config')
    args = parser.parse_args()

    set_seed(42)

    timestamps, values = load_and_validate_data(args.data)
    threshold = load_threshold_config(args.config)

    anomalies = detect_anomalies(values, threshold)
    save_predictions(timestamps, anomalies, args.output)
    print_summary(anomalies)

    logger.info("CUSUM detection completed.")

if __name__ == '__main__':
    main()
