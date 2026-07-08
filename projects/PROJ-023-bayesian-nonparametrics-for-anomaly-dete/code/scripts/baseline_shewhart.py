"""
Shewhart Control Chart for Time Series Anomaly Detection

Implements a classical statistical process control method that flags
observations outside mean ± k*standard_deviation as anomalies.

Input:  data/processed/series_with_anomalies.csv
Output: data/results/shewhart_predictions.csv

This script implements User Story 2 (Baseline Comparison Engine) for the
Bayesian Nonparametrics for Anomaly Detection project.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
DATA_PATH = Path("data/processed/series_with_anomalies.csv")
OUTPUT_PATH = Path("data/results/shewhart_predictions.csv")
SIGMA_THRESHOLD = 3.0  # Standard control chart limit (99.7% coverage)
NORMAL_ESTIMATE_FRACTION = 0.8  # Assume first 80% is mostly normal

def load_and_validate_data(data_path: Path) -> tuple[np.ndarray, np.ndarray]:
    """
    Load time series data and extract values and indices.
    
    Args:
        data_path: Path to the CSV file containing time series data
        
    Returns:
        Tuple of (values array, indices array)
        
    Raises:
        FileNotFoundError: If data file doesn't exist
        ValueError: If data format is invalid
    """
    if not data_path.exists():
        raise FileNotFoundError(f"Data file not found: {data_path}")
    
    logger.info(f"Loading data from {data_path}")
    df = pd.read_csv(data_path)
    
    # Handle different column formats
    if 'value' in df.columns:
        series = df['value'].values.astype(np.float64)
        # Use 'index' column if present, otherwise use DataFrame index
        if 'index' in df.columns:
            indices = df['index'].values
        else:
            indices = np.arange(len(series))
    elif len(df.columns) == 1:
        series = df.iloc[:, 0].values.astype(np.float64)
        indices = np.arange(len(series))
    else:
        # Use first numeric column
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) == 0:
            raise ValueError("No numeric columns found in data")
        series = df[numeric_cols[0]].values.astype(np.float64)
        indices = df.index.values
    
    # Validate data
    if len(series) == 0:
        raise ValueError("Data series is empty")
    
    if np.any(np.isnan(series)):
        logger.warning("NaN values detected in data. Dropping them.")
        valid_mask = ~np.isnan(series)
        series = series[valid_mask]
        indices = indices[valid_mask]
    
    logger.info(f"Loaded {len(series)} data points")
    return series, indices

def calculate_control_limits(series: np.ndarray, sigma: float, 
                             normal_fraction: float) -> tuple[float, float, float, float]:
    """
    Calculate control limits based on baseline statistics.
    
    Uses the first portion of the data (assumed mostly normal) to estimate
    mean and standard deviation.
    
    Args:
        series: Time series values
        sigma: Number of standard deviations for control limits
        normal_fraction: Fraction of data to use for baseline estimation
        
    Returns:
        Tuple of (mean, std, upper_limit, lower_limit)
    """
    n_normal_estimate = int(len(series) * normal_fraction)
    
    # Ensure we have at least 10 points for baseline estimation
    n_normal_estimate = max(n_normal_estimate, 10)
    
    baseline_data = series[:n_normal_estimate]
    
    mean = np.mean(baseline_data)
    std = np.std(baseline_data)
    
    # Handle edge case where std is zero or very small
    if std < 1e-10:
        logger.warning("Baseline standard deviation is near zero. Setting to 1.0")
        std = 1.0
    
    upper_limit = mean + sigma * std
    lower_limit = mean - sigma * std
    
    logger.info(f"Baseline mean: {mean:.4f}, std: {std:.4f}")
    logger.info(f"Control limits: [{lower_limit:.4f}, {upper_limit:.4f}]")
    
    return mean, std, upper_limit, lower_limit

def detect_anomalies(series: np.ndarray, upper_limit: float, 
                    lower_limit: float) -> np.ndarray:
    """
    Detect anomalies based on control limits.
    
    Args:
        series: Time series values
        upper_limit: Upper control limit
        lower_limit: Lower control limit
        
    Returns:
        Binary array indicating anomalies (1) and normal points (0)
    """
    anomaly_flags = ((series > upper_limit) | (series < lower_limit)).astype(int)
    return anomaly_flags

def calculate_z_scores(series: np.ndarray, mean: float, std: float) -> np.ndarray:
    """
    Calculate z-scores for each point.
    
    Args:
        series: Time series values
        mean: Baseline mean
        std: Baseline standard deviation
        
    Returns:
        Array of z-scores
    """
    # Avoid division by zero
    if std < 1e-10:
        std = 1.0
    z_scores = (series - mean) / std
    return z_scores

def save_predictions(indices: np.ndarray, series: np.ndarray, mean: float,
                    std: float, upper_limit: float, lower_limit: float,
                    z_scores: np.ndarray, anomaly_flags: np.ndarray,
                    output_path: Path):
    """
    Save predictions to CSV file.
    
    Args:
        indices: Time indices
        series: Time series values
        mean: Baseline mean
        std: Baseline standard deviation
        upper_limit: Upper control limit
        lower_limit: Lower control limit
        z_scores: Z-scores for each point
        anomaly_flags: Binary anomaly flags
        output_path: Path to save the predictions
    """
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    predictions = pd.DataFrame({
        'index': indices,
        'value': series,
        'mean': mean,
        'std': std,
        'upper_limit': upper_limit,
        'lower_limit': lower_limit,
        'z_score': z_scores,
        'anomaly': anomaly_flags
    })
    
    predictions.to_csv(output_path, index=False)
    logger.info(f"Predictions saved to {output_path}")

def print_summary(series: np.ndarray, anomaly_flags: np.ndarray, 
                 mean: float, std: float, upper_limit: float, 
                 lower_limit: float):
    """
    Print summary statistics to console.
    
    Args:
        series: Time series values
        anomaly_flags: Binary anomaly flags
        mean: Baseline mean
        std: Baseline standard deviation
        upper_limit: Upper control limit
        lower_limit: Lower control limit
    """
    n_anomalies = int(anomaly_flags.sum())
    anomaly_rate = n_anomalies / len(series) * 100
    
    print("\n" + "="*60)
    print("Shewhart Control Chart Results")
    print("="*60)
    print(f"Baseline mean:        {mean:.4f}")
    print(f"Baseline std:         {std:.4f}")
    print(f"Upper control limit:  {upper_limit:.4f}")
    print(f"Lower control limit:  {lower_limit:.4f}")
    print(f"Sigma threshold:      {SIGMA_THRESHOLD}σ")
    print("-"*60)
    print(f"Total points analyzed: {len(series)}")
    print(f"Anomalies detected:    {n_anomalies}")
    print(f"Anomaly rate:          {anomaly_rate:.2f}%")
    print("="*60 + "\n")

def main():
    """
    Main entry point for the Shewhart baseline detection script.
    """
    try:
        # Load and validate data
        series, indices = load_and_validate_data(DATA_PATH)
        
        # Calculate control limits
        mean, std, upper_limit, lower_limit = calculate_control_limits(
            series, SIGMA_THRESHOLD, NORMAL_ESTIMATE_FRACTION
        )
        
        # Detect anomalies
        anomaly_flags = detect_anomalies(series, upper_limit, lower_limit)
        
        # Calculate z-scores
        z_scores = calculate_z_scores(series, mean, std)
        
        # Save predictions
        save_predictions(
            indices, series, mean, std, upper_limit, lower_limit,
            z_scores, anomaly_flags, OUTPUT_PATH
        )
        
        # Print summary
        print_summary(series, anomaly_flags, mean, std, upper_limit, lower_limit)
        
        logger.info("Shewhart baseline detection completed successfully")
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"Data file error: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Data validation error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())