import numpy as np
import pandas as pd
from typing import List, Tuple, Dict, Optional
from scipy import stats
from pathlib import Path
import os
import logging

# Import project paths from config
from src.config import get_data_root
from src.utils import write_csv, read_csv

logger = logging.getLogger(__name__)

def pearson_correlation(x: List[float], y: List[float]) -> float:
    """Calculate Pearson correlation coefficient."""
    if len(x) != len(y) or len(x) < 2:
        return 0.0
    return float(stats.pearsonr(x, y)[0])

def spearman_correlation(x: List[float], y: List[float]) -> float:
    """Calculate Spearman rank correlation coefficient."""
    if len(x) != len(y) or len(x) < 2:
        return 0.0
    return float(stats.spearmanr(x, y)[0])

def bootstrap_confidence_interval(
    x: List[float],
    y: List[float],
    n_iterations: int = 1000,
    alpha: float = 0.05,
    method: str = "pearson"
) -> Tuple[float, float, float]:
    """
    Calculate bootstrap confidence interval for correlation.

    Returns: (correlation, lower_ci, upper_ci)
    """
    if len(x) != len(y) or len(x) < 2:
        return 0.0, 0.0, 0.0

    n = len(x)
    correlations = []

    for _ in range(n_iterations):
        indices = np.random.choice(n, size=n, replace=True)
        x_boot = [x[i] for i in indices]
        y_boot = [y[i] for i in indices]

        if method == "pearson":
            corr = pearson_correlation(x_boot, y_boot)
        else:
            corr = spearman_correlation(x_boot, y_boot)

        correlations.append(corr)

    correlations = np.array(correlations)
    corr_mean = float(np.mean(correlations))
    lower = float(np.percentile(correlations, 100 * alpha / 2))
    upper = float(np.percentile(correlations, 100 * (1 - alpha / 2)))

    return corr_mean, lower, upper

def classify_dimension_status(
    correlation: float,
    lower_ci: float,
    threshold_high: float = 0.85
) -> str:
    """
    Classify a dimension based on correlation and CI.

    Rules:
    - "feature-sufficient": r >= 0.85
    - "VLM-required": lower 95% CI < 0.70
    - "uncertain": otherwise
    """
    if correlation >= threshold_high:
        return "feature-sufficient"
    elif lower_ci < 0.70:
        return "VLM-required"
    else:
        return "uncertain"

def run_threshold_sweep(
    correlation_results_path: Optional[str] = None,
    thresholds: Optional[List[float]] = None,
    output_path: Optional[str] = None
) -> pd.DataFrame:
    """
    Perform threshold sweep analysis on correlation results.

    Loads dimension-level correlation results (from T017) and evaluates
    classification status at multiple thresholds.

    Args:
        correlation_results_path: Path to the CSV containing dimension correlations.
                                  If None, uses default path from config.
        thresholds: List of thresholds to test. Defaults to [0.80, 0.85, 0.90].
        output_path: Path to write the raw sweep results. If None, uses default.

    Returns:
        DataFrame with columns: [dimension, threshold, status]
    """
    if thresholds is None:
        thresholds = [0.80, 0.85, 0.90]

    # Default paths
    data_root = get_data_root()
    if correlation_results_path is None:
        correlation_results_path = os.path.join(data_root, "results", "dimension_correlations.csv")
    
    if output_path is None:
        output_path = os.path.join(data_root, "sensitivity_sweep_raw.csv")

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Load correlation results
    if not os.path.exists(correlation_results_path):
        raise FileNotFoundError(
            f"Correlation results file not found: {correlation_results_path}. "
            "Prerequisite T017 must complete first."
        )

    df = pd.read_csv(correlation_results_path)

    required_cols = ['dimension', 'correlation', 'lower_ci', 'upper_ci']
    if not all(col in df.columns for col in required_cols):
        missing = [col for col in required_cols if col not in df.columns]
        raise ValueError(f"Missing required columns in {correlation_results_path}: {missing}")

    results = []

    for _, row in df.iterrows():
        dimension = row['dimension']
        correlation = row['correlation']
        lower_ci = row['lower_ci']

        for threshold in thresholds:
            # Determine status based on the threshold
            # "feature-sufficient" if r >= threshold
            # "VLM-required" if lower_ci < 0.70
            # "uncertain" otherwise
            if correlation >= threshold:
                status = "feature-sufficient"
            elif lower_ci < 0.70:
                status = "VLM-required"
            else:
                status = "uncertain"

            results.append({
                'dimension': dimension,
                'threshold': threshold,
                'status': status
            })

    result_df = pd.DataFrame(results)
    
    # Ensure column order
    result_df = result_df[['dimension', 'threshold', 'status']]
    
    # Write to CSV
    write_csv(result_df, output_path)
    logger.info(f"Threshold sweep completed. Results written to: {output_path}")
    
    return result_df

def main():
    """Entry point for running threshold sweep analysis."""
    logging.basicConfig(level=logging.INFO)
    
    try:
        df = run_threshold_sweep()
        print(f"Sensitivity sweep raw data generated with {len(df)} rows.")
        print(df.head())
    except Exception as e:
        logger.error(f"Threshold sweep failed: {e}")
        raise
