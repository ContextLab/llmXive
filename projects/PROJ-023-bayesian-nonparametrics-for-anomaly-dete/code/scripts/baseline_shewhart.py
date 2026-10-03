"""
Shewhart Control Chart Baseline for Anomaly Detection.

Implements a standard Shewhart chart with configurable sigma control limits.
Uses the shared data loader from T004 to ingest real time series data.
Outputs anomaly scores and binary flags to data/results/shewhart_predictions.csv.
"""
import os
import sys
import logging
import argparse
from pathlib import Path
from typing import Tuple, Dict, Any, Optional

import pandas as pd
import numpy as np

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from lib.data_loader import load_processed_data
from lib.utils import set_seed, normalize_series, handle_missing_values
from lib.memory_profiler import check_memory_usage, MemoryProfiler

logger = logging.getLogger(__name__)

def load_and_validate_data(data_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Load processed time series data and validate its structure.

    Args:
        data_path: Path to the processed CSV file. If None, uses default location.

    Returns:
        DataFrame with 'timestamp' and 'value' columns.

    Raises:
        FileNotFoundError: If the data file does not exist.
        ValueError: If the schema is invalid.
    """
    if data_path is None:
        data_path = PROJECT_ROOT / "data" / "processed" / "series_with_anomalies.csv"

    if not data_path.exists():
        raise FileNotFoundError(f"Processed data not found at {data_path}. "
                                f"Run data loading/injection tasks first.")

    df = pd.read_csv(data_path)

    # Validate schema
    required_cols = {'timestamp', 'value'}
    if not required_cols.issubset(df.columns):
        raise ValueError(f"DataFrame missing required columns {required_cols}. "
                         f"Found: {df.columns.tolist()}")

    # Ensure numeric type for values
    df['value'] = pd.to_numeric(df['value'], errors='raise')

    logger.info(f"Loaded {len(df)} rows from {data_path}")
    return df

def calculate_control_limits(
    values: np.ndarray,
    sigma_factor: float = 3.0
) -> Tuple[float, float, float]:
    """
    Calculate Shewhart control limits based on the training data statistics.

    Args:
        values: Array of time series values.
        sigma_factor: Number of standard deviations for control limits (default 3.0).

    Returns:
        Tuple of (center_line, upper_control_limit, lower_control_limit).
    """
    center_line = np.mean(values)
    std_dev = np.std(values, ddof=1) # Sample standard deviation

    ucl = center_line + (sigma_factor * std_dev)
    lcl = center_line - (sigma_factor * std_dev)

    logger.info(f"Calculated limits: CL={center_line:.4f}, UCL={ucl:.4f}, LCL={lcl:.4f} "
                f"(sigma={sigma_factor})")

    return center_line, ucl, lcl

def calculate_z_scores(
    values: np.ndarray,
    center_line: float,
    std_dev: float
) -> np.ndarray:
    """
    Calculate z-scores for each point relative to the center line and standard deviation.

    Args:
        values: Array of time series values.
        center_line: The mean of the series.
        std_dev: The standard deviation of the series.

    Returns:
        Array of z-scores.
    """
    if std_dev == 0:
        # Avoid division by zero; if std is 0, all points are equal to mean (z=0)
        return np.zeros_like(values, dtype=float)
    return (values - center_line) / std_dev

def detect_anomalies(
    z_scores: np.ndarray,
    threshold: float = 3.0
) -> np.ndarray:
    """
    Detect anomalies based on absolute z-scores exceeding the threshold.

    Args:
        z_scores: Array of calculated z-scores.
        threshold: Absolute z-score threshold (default 3.0).

    Returns:
        Binary array (1 for anomaly, 0 for normal).
    """
    return (np.abs(z_scores) > threshold).astype(int)

def save_predictions(
    df: pd.DataFrame,
    predictions: np.ndarray,
    z_scores: np.ndarray,
    output_path: Path
) -> None:
    """
    Save predictions and scores to a CSV file.

    Args:
        df: Original DataFrame with timestamps.
        predictions: Binary anomaly flags.
        z_scores: Calculated z-scores.
        output_path: Path to save the output CSV.
    """
    output_df = pd.DataFrame({
        'timestamp': df['timestamp'],
        'value': df['value'],
        'z_score': z_scores,
        'anomaly_flag': predictions
    })

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_df.to_csv(output_path, index=False)
    logger.info(f"Saved predictions to {output_path}")

def print_summary(
    predictions: np.ndarray,
    total_points: int
) -> None:
    """Print a summary of the detection results."""
    anomaly_count = np.sum(predictions)
    anomaly_rate = anomaly_count / total_points * 100
    print(f"\n--- Shewhart Detection Summary ---")
    print(f"Total points: {total_points}")
    print(f"Anomalies detected: {anomaly_count} ({anomaly_rate:.2f}%)")
    print(f"----------------------------------")

def load_threshold_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load threshold configuration from YAML file.

    Args:
        config_path: Path to the config file. Defaults to project config.

    Returns:
        Dictionary with configuration parameters.
    """
    if config_path is None:
        config_path = PROJECT_ROOT / "code" / "config" / "threshold_strategy.yaml"

    if not config_path.exists():
        logger.warning(f"Config file not found at {config_path}. Using defaults.")
        return {"sigma_factor": 3.0}

    import yaml
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    # Extract sigma factor if available, otherwise default to 3.0
    sigma_factor = config.get('sigma_factor', 3.0)
    return {"sigma_factor": sigma_factor}

def main() -> int:
    """
    Main entry point for the Shewhart baseline script.
    """
    parser = argparse.ArgumentParser(description="Run Shewhart baseline anomaly detection.")
    parser.add_argument(
        "--data-path",
        type=str,
        default=None,
        help="Path to processed data CSV. Defaults to data/processed/series_with_anomalies.csv"
    )
    parser.add_argument(
        "--output-path",
        type=str,
        default=None,
        help="Path for output CSV. Defaults to data/results/shewhart_predictions.csv"
    )
    parser.add_argument(
        "--sigma",
        type=float,
        default=None,
        help="Sigma factor for control limits. Overrides config if provided."
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility."
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging."
    )

    args = parser.parse_args()

    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Pin seed
    set_seed(args.seed)

    # Initialize memory profiler
    profiler = MemoryProfiler(limit_gb=7.0)
    profiler.start()

    try:
        # 1. Load Configuration
        config = load_threshold_config()
        sigma_factor = args.sigma if args.sigma is not None else config.get('sigma_factor', 3.0)
        logger.info(f"Using sigma factor: {sigma_factor}")

        # 2. Load Data
        data_path = Path(args.data_path) if args.data_path else None
        df = load_and_validate_data(data_path)

        # Handle missing values (interpolation policy)
        df['value'] = handle_missing_values(df['value'], policy='interpolate')

        # 3. Calculate Statistics
        values = df['value'].to_numpy()
        center_line, ucl, lcl = calculate_control_limits(values, sigma_factor)
        std_dev = np.std(values, ddof=1)

        # 4. Calculate Z-Scores and Detect Anomalies
        z_scores = calculate_z_scores(values, center_line, std_dev)
        predictions = detect_anomalies(z_scores, threshold=sigma_factor)

        # 5. Save Results
        output_path = Path(args.output_path) if args.output_path else (PROJECT_ROOT / "data" / "results" / "shewhart_predictions.csv")
        save_predictions(df, predictions, z_scores, output_path)

        # 6. Print Summary
        print_summary(predictions, len(df))

        # 7. Check Memory
        profiler.stop()
        if profiler.peak_gb > profiler.limit_gb:
            logger.error(f"Memory limit exceeded: {profiler.peak_gb:.2f}GB > {profiler.limit_gb}GB")
            return 1

        return 0

    except Exception as e:
        logger.exception(f"Error during Shewhart execution: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())