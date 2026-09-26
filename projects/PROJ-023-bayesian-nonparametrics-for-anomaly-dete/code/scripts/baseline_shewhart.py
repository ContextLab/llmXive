"""
Shewhart Control Chart Baseline for Anomaly Detection.

Implements a standard Shewhart control chart using 3-sigma limits
on the time series data loaded from the shared data loader.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging
import sys
import argparse
from typing import Tuple, Optional, Dict, Any, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_and_validate_data(input_path: str) -> pd.DataFrame:
    """
    Load time series data and validate schema.

    Args:
        input_path: Path to the processed time series CSV.

    Returns:
        DataFrame with columns: ['timestamp', 'value', 'ground_truth']

    Raises:
        SystemExit: If file not found or schema invalid.
    """
    logger.info(f"Loading data from {input_path}")
    path = Path(input_path)
    if not path.exists():
        logger.error(f"Input file not found: {input_path}")
        raise SystemExit(1)

    try:
        df = pd.read_csv(path)
    except Exception as e:
        logger.error(f"Failed to read CSV: {e}")
        raise SystemExit(1)

    # Validate schema based on T004/T005 expectations
    required_cols = {'timestamp', 'value', 'ground_truth'}
    if not required_cols.issubset(df.columns):
        logger.error(f"Missing required columns. Expected: {required_cols}, Found: {df.columns.tolist()}")
        raise SystemExit(1)

    # Handle missing values in 'value' column
    if df['value'].isna().any():
        logger.warning("Missing values detected in 'value' column. Interpolating linearly.")
        df['value'] = df['value'].interpolate(method='linear')
        df['value'] = df['value'].ffill().bfill()  # Handle edges

    if df['value'].isna().any():
        logger.error("Could not resolve all missing values.")
        raise SystemExit(1)

    logger.info(f"Data loaded successfully. Shape: {df.shape}")
    return df

def calculate_control_limits(df: pd.DataFrame, sigma_multiplier: float = 3.0) -> Tuple[float, float, float]:
    """
    Calculate Shewhart control limits (UCL, LCL, CL).

    Args:
        df: DataFrame with 'value' column.
        sigma_multiplier: Number of standard deviations for limits (default 3.0).

    Returns:
        Tuple of (CL, UCL, LCL).
    """
    mean = df['value'].mean()
    std = df['value'].std()

    if std == 0:
        logger.warning("Standard deviation is zero. Setting limits equal to mean.")
        std = 1e-6

    cl = mean
    ucl = mean + (sigma_multiplier * std)
    lcl = mean - (sigma_multiplier * std)

    logger.info(f"Control Limits calculated: CL={cl:.4f}, UCL={ucl:.4f}, LCL={lcl:.4f} (sigma={sigma_multiplier})")
    return cl, ucl, lcl

def calculate_z_scores(df: pd.DataFrame, cl: float, std: float) -> pd.Series:
    """
    Calculate z-scores for each point relative to the control mean.

    Args:
        df: DataFrame with 'value' column.
        cl: Control limit mean.
        std: Standard deviation of the series.

    Returns:
        Series of z-scores.
    """
    return (df['value'] - cl) / std

def detect_anomalies(df: pd.DataFrame, ucl: float, lcl: float) -> pd.Series:
    """
    Detect anomalies based on Shewhart rules.

    Args:
        df: DataFrame with 'value' column.
        ucl: Upper Control Limit.
        lcl: Lower Control Limit.

    Returns:
        Boolean Series where True indicates an anomaly.
    """
    anomalies = (df['value'] > ucl) | (df['value'] < lcl)
    return anomalies

def save_predictions(df: pd.DataFrame, output_path: str, anomalies: pd.Series) -> None:
    """
    Save predictions to CSV.

    Args:
        df: Original DataFrame.
        output_path: Path to save the output CSV.
        anomalies: Boolean Series of detected anomalies.
    """
    output_df = df.copy()
    output_df['predicted_anomaly'] = anomalies.astype(int)
    output_df['method'] = 'shewhart'

    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    output_df.to_csv(output_path, index=False)
    logger.info(f"Predictions saved to {output_path}")

def print_summary(df: pd.DataFrame, anomalies: pd.Series, cl: float, ucl: float, lcl: float) -> None:
    """
    Print a summary of the detection results.

    Args:
        df: Original DataFrame.
        anomalies: Boolean Series of detected anomalies.
        cl: Control Limit mean.
        ucl: Upper Control Limit.
        lcl: Lower Control Limit.
    """
    total_points = len(df)
    detected_count = anomalies.sum()
    detected_rate = (detected_count / total_points) * 100

    print("\n--- Shewhart Detection Summary ---")
    print(f"Total Data Points: {total_points}")
    print(f"Control Mean (CL): {cl:.4f}")
    print(f"Upper Control Limit (UCL): {ucl:.4f}")
    print(f"Lower Control Limit (LCL): {lcl:.4f}")
    print(f"Anomalies Detected: {detected_count} ({detected_rate:.2f}%)")
    print("--------------------------------\n")

def main() -> None:
    """Main entry point for the Shewhart baseline script."""
    parser = argparse.ArgumentParser(description="Run Shewhart Control Chart Anomaly Detection")
    parser.add_argument(
        "--input",
        type=str,
        default="data/processed/series_with_anomalies.csv",
        help="Path to the input processed time series CSV"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/results/shewhart_predictions.csv",
        help="Path to save the output predictions CSV"
    )
    parser.add_argument(
        "--sigma",
        type=float,
        default=3.0,
        help="Sigma multiplier for control limits (default: 3.0)"
    )

    args = parser.parse_args()

    try:
        # 1. Load and Validate
        df = load_and_validate_data(args.input)

        # 2. Calculate Control Limits
        cl, ucl, lcl = calculate_control_limits(df, sigma_multiplier=args.sigma)

        # 3. Detect Anomalies
        anomalies = detect_anomalies(df, ucl, lcl)

        # 4. Save Predictions
        save_predictions(df, args.output, anomalies)

        # 5. Print Summary
        print_summary(df, anomalies, cl, ucl, lcl)

        logger.info("Shewhart baseline execution completed successfully.")

    except SystemExit:
        logger.error("Shewhart baseline execution failed.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during execution: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()