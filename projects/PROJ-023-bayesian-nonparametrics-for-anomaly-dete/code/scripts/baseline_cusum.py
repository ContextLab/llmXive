"""
CUSUM (Cumulative Sum) Baseline for Anomaly Detection.

Implements a two-sided CUSUM algorithm for change point detection in time series.
Outputs anomaly scores and binary flags to data/results/cusum_predictions.csv.
"""

import os
import sys
import logging
import argparse
from pathlib import Path
from typing import Tuple, Optional

import numpy as np
import pandas as pd

# Add project root to path to ensure imports work in both dev and execution contexts
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from lib.data_loader import load_time_series
from lib.utils import set_seed, profile_memory_enforcement, MemoryProfiler
from lib.metrics import precision_recall_f1

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
MEMORY_LIMIT_GB = 7.0
DEFAULT_THRESHOLD_FACTOR = 5.0  # h = k * sigma, where k is threshold_factor
DEFAULT_K_FACTOR = 0.5          # Reference value k = 0.5 * sigma

def load_and_validate_data(
    data_path: Path,
    ground_truth_path: Optional[Path] = None
) -> Tuple[pd.DataFrame, Optional[pd.DataFrame]]:
    """
    Load time series data and optional ground truth.

    Args:
        data_path: Path to the processed time series CSV.
        ground_truth_path: Optional path to ground truth CSV.

    Returns:
        Tuple of (dataframe with series, optional ground truth dataframe)
    """
    logger.info(f"Loading data from {data_path}")
    
    if not data_path.exists():
        raise FileNotFoundError(f"Data file not found: {data_path}")
    
    df = load_time_series(data_path)
    
    if ground_truth_path and ground_truth_path.exists():
        logger.info(f"Loading ground truth from {ground_truth_path}")
        ground_truth = pd.read_csv(ground_truth_path)
        # Ensure alignment
        if len(df) != len(ground_truth):
            logger.warning("Length mismatch between data and ground truth. Attempting to align by index.")
            ground_truth = ground_truth.iloc[:len(df)]
        return df, ground_truth
    
    return df, None

def calculate_cusum_parameters(
    data: np.ndarray,
    k_factor: float = DEFAULT_K_FACTOR
) -> Tuple[float, float, float]:
    """
    Calculate CUSUM parameters (mean, sigma, reference value k, threshold h).

    Args:
        data: Time series data array.
        k_factor: Factor for reference value k relative to sigma.

    Returns:
        Tuple of (mean, sigma, k, h)
    """
    mean = np.mean(data)
    sigma = np.std(data)
    
    # Reference value k (usually 0.5 * sigma for detecting shifts of 1 sigma)
    k = k_factor * sigma
    
    # Threshold h (usually 4-5 * sigma for good detection performance)
    # We'll use a factor that can be tuned, defaulting to 5.0
    h = DEFAULT_THRESHOLD_FACTOR * sigma
    
    logger.info(f"Calculated CUSUM parameters: mean={mean:.4f}, sigma={sigma:.4f}, k={k:.4f}, h={h:.4f}")
    
    return mean, sigma, k, h

def run_cusum_detection(
    data: np.ndarray,
    mean: float,
    sigma: float,
    k: float,
    h: float
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Run CUSUM algorithm for anomaly detection.

    Implements two-sided CUSUM:
    S_H[i] = max(0, S_H[i-1] + (x[i] - mean) - k)
    S_L[i] = max(0, S_L[i-1] - (x[i] - mean) - k)
    Anomaly if S_H[i] > h or S_L[i] > h

    Args:
        data: Time series data.
        mean: Mean of the data.
        sigma: Standard deviation of the data.
        k: Reference value.
        h: Threshold.

    Returns:
        Tuple of (anomaly_scores, binary_flags)
    """
    n = len(data)
    s_pos = np.zeros(n)  # Upper CUSUM
    s_neg = np.zeros(n)  # Lower CUSUM
    
    # Scores will be the maximum of the two CUSUM statistics
    scores = np.zeros(n)
    flags = np.zeros(n, dtype=int)
    
    for i in range(1, n):
        # Update upper CUSUM (detects upward shifts)
        s_pos[i] = max(0, s_pos[i-1] + (data[i] - mean) - k)
        
        # Update lower CUSUM (detects downward shifts)
        s_neg[i] = max(0, s_neg[i-1] - (data[i] - mean) - k)
        
        # Anomaly score is the maximum of the two
        scores[i] = max(s_pos[i], s_neg[i])
        
        # Binary flag if either exceeds threshold
        if s_pos[i] > h or s_neg[i] > h:
            flags[i] = 1
        else:
            flags[i] = 0
    
    # First point is never flagged (no history)
    scores[0] = 0.0
    flags[0] = 0
    
    logger.info(f"CUSUM detection complete. Detected {sum(flags)} anomalies out of {n} points.")
    
    return scores, flags

def save_predictions(
    data: pd.DataFrame,
    scores: np.ndarray,
    flags: np.ndarray,
    output_path: Path,
    parameters: dict
) -> None:
    """
    Save predictions to CSV.

    Args:
        data: Original data dataframe.
        scores: Anomaly scores.
        flags: Binary anomaly flags.
        output_path: Path to output file.
        parameters: Dictionary of parameters used.
    """
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create output dataframe
    output_df = pd.DataFrame({
        'timestamp': data.index if hasattr(data, 'index') else range(len(data)),
        'value': data.iloc[:, 0].values if data.shape[1] == 1 else data.values.flatten(),
        'cusum_score': scores,
        'is_anomaly': flags
    })
    
    output_df.to_csv(output_path, index=False)
    logger.info(f"Predictions saved to {output_path}")
    
    # Log parameters used
    logger.info(f"Parameters: {parameters}")

def print_summary(
    data: np.ndarray,
    scores: np.ndarray,
    flags: np.ndarray,
    ground_truth: Optional[pd.DataFrame] = None
) -> None:
    """
    Print summary statistics of the detection results.

    Args:
        data: Original data.
        scores: Anomaly scores.
        flags: Binary flags.
        ground_truth: Optional ground truth for evaluation.
    """
    logger.info("=== CUSUM Detection Summary ===")
    logger.info(f"Data points: {len(data)}")
    logger.info(f"Anomalies detected: {sum(flags)} ({100*sum(flags)/len(data):.2f}%)")
    logger.info(f"Score range: [{scores.min():.4f}, {scores.max():.4f}]")
    logger.info(f"Score mean: {scores.mean():.4f}")
    
    if ground_truth is not None:
        # Assume ground truth has a column 'is_anomaly' or similar
        gt_col = 'is_anomaly' if 'is_anomaly' in ground_truth.columns else ground_truth.columns[1]
        gt_labels = ground_truth[gt_col].values[:len(flags)]
        
        if len(gt_labels) == len(flags):
            precision, recall, f1 = precision_recall_f1(flags, gt_labels)
            logger.info(f"Precision: {precision:.4f}")
            logger.info(f"Recall: {recall:.4f}")
            logger.info(f"F1 Score: {f1:.4f}")
        else:
            logger.warning("Ground truth length mismatch, skipping metrics.")

def main(
    data_path: Optional[str] = None,
    ground_truth_path: Optional[str] = None,
    output_path: Optional[str] = None,
    k_factor: float = DEFAULT_K_FACTOR,
    threshold_factor: float = DEFAULT_THRESHOLD_FACTOR,
    seed: int = 42
) -> None:
    """
    Main entry point for CUSUM baseline detection.

    Args:
        data_path: Path to input data CSV.
        ground_truth_path: Optional path to ground truth CSV.
        output_path: Path to output predictions CSV.
        k_factor: Factor for reference value k.
        threshold_factor: Factor for threshold h.
        seed: Random seed for reproducibility.
    """
    set_seed(seed)
    
    # Default paths
    if data_path is None:
        data_path = str(project_root / "data" / "processed" / "series_with_anomalies.csv")
    if output_path is None:
        output_path = str(project_root / "data" / "results" / "cusum_predictions.csv")
    
    data_path = Path(data_path)
    output_path = Path(output_path)
    ground_truth_path = Path(ground_truth_path) if ground_truth_path else None
    
    # Memory profiling
    profiler = MemoryProfiler(limit_gb=MEMORY_LIMIT_GB)
    
    with profiler:
        # Load data
        df, ground_truth = load_and_validate_data(data_path, ground_truth_path)
        
        if df.empty:
            raise ValueError("Loaded data is empty.")
        
        # Extract time series values (assume first column is the series)
        series = df.iloc[:, 0].values.astype(float)
        
        logger.info(f"Processing {len(series)} data points")
        
        # Calculate parameters
        mean, sigma, k, h = calculate_cusum_parameters(series, k_factor)
        
        # Run detection
        scores, flags = run_cusum_detection(series, mean, sigma, k, h)
        
        # Save results
        parameters = {
            'k_factor': k_factor,
            'threshold_factor': threshold_factor,
            'mean': float(mean),
            'sigma': float(sigma),
            'k': float(k),
            'h': float(h)
        }
        save_predictions(df, scores, flags, output_path, parameters)
        
        # Print summary
        print_summary(series, scores, flags, ground_truth)
    
    # Check memory usage
    if profiler.peak_memory_gb > MEMORY_LIMIT_GB:
        logger.error(f"Memory limit exceeded: {profiler.peak_memory_gb:.2f}GB > {MEMORY_LIMIT_GB}GB")
        sys.exit(1)
    else:
        logger.info(f"Memory usage OK: {profiler.peak_memory_gb:.2f}GB <= {MEMORY_LIMIT_GB}GB")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CUSUM Baseline for Anomaly Detection")
    parser.add_argument("--data", type=str, help="Path to input data CSV")
    parser.add_argument("--ground-truth", type=str, help="Path to ground truth CSV")
    parser.add_argument("--output", type=str, help="Path to output predictions CSV")
    parser.add_argument("--k-factor", type=float, default=DEFAULT_K_FACTOR, help="Factor for reference value k")
    parser.add_argument("--threshold-factor", type=float, default=DEFAULT_THRESHOLD_FACTOR, help="Factor for threshold h")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    
    args = parser.parse_args()
    
    main(
        data_path=args.data,
        ground_truth_path=args.ground_truth,
        output_path=args.output,
        k_factor=args.k_factor,
        threshold_factor=args.threshold_factor,
        seed=args.seed
    )