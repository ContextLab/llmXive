"""
Module to compute and output Minimum Detectable Concentration (MDC) statistics.

This task (T030c) aggregates the MDC values derived during the retrieval phase (T019)
and computes summary statistics (mean, median, std, percentiles) for the dataset.
It addresses the requirement to quantify the sensitivity of the analysis.
"""
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List

import pandas as pd
import numpy as np

from config import get_config
from utils import setup_logging

# Configure logging
logger = setup_logging("mdc_stats")

def load_retrieval_results(config: Dict[str, Any]) -> pd.DataFrame:
    """
    Load the retrieval results CSV containing MDC values.
    
    Args:
        config: Configuration dictionary containing paths.
        
    Returns:
        DataFrame with retrieval results.
        
    Raises:
        FileNotFoundError: If the retrieval results file does not exist.
    """
    results_path = Path(config["paths"]["data_processed"]) / "retrieval_results.csv"
    
    if not results_path.exists():
        raise FileNotFoundError(
            f"Retrieval results file not found at {results_path}. "
            "Please ensure T020 has been completed successfully."
        )
    
    df = pd.read_csv(results_path)
    
    required_cols = ["water_mixing_ratio", "is_upper_limit", "min_detectable_concentration"]
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(
            f"Missing required columns in retrieval results: {missing_cols}"
        )
    
    return df

def compute_mdc_statistics(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Compute summary statistics for the Minimum Detectable Concentration (MDC).
    
    Calculates mean, median, standard deviation, and percentiles (10th, 50th, 90th)
    for the MDC values. Also counts the number of detections vs upper limits.
    
    Args:
        df: DataFrame containing retrieval results with 'min_detectable_concentration'.
        
    Returns:
        Dictionary containing computed statistics.
    """
    mdc_series = df["min_detectable_concentration"]
    
    # Filter out NaN or infinite values if any
    valid_mdc = mdc_series.dropna()
    valid_mdc = valid_mdc[np.isfinite(valid_mdc)]
    
    if len(valid_mdc) == 0:
        logger.warning("No valid MDC values found in the dataset.")
        stats = {
            "count": 0,
            "mean": None,
            "median": None,
            "std": None,
            "percentile_10": None,
            "percentile_50": None,
            "percentile_90": None,
            "min": None,
            "max": None
        }
    else:
        stats = {
            "count": int(len(valid_mdc)),
            "mean": float(np.mean(valid_mdc)),
            "median": float(np.median(valid_mdc)),
            "std": float(np.std(valid_mdc)),
            "percentile_10": float(np.percentile(valid_mdc, 10)),
            "percentile_50": float(np.percentile(valid_mdc, 50)),
            "percentile_90": float(np.percentile(valid_mdc, 90)),
            "min": float(np.min(valid_mdc)),
            "max": float(np.max(valid_mdc))
        }
    
    # Count breakdown
    total = len(df)
    upper_limits = int(df["is_upper_limit"].sum())
    detections = total - upper_limits
    
    stats["total_spectra"] = total
    stats["upper_limits_count"] = upper_limits
    stats["detections_count"] = detections
    
    logger.info(f"Computed MDC statistics for {stats['count']} valid entries.")
    
    return stats

def save_mdc_stats(stats: Dict[str, Any], output_path: Path) -> None:
    """
    Save the MDC statistics to a JSON file.
    
    Args:
        stats: Dictionary of statistics to save.
        output_path: Path to the output JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)
    
    logger.info(f"MDC statistics saved to {output_path}")

def main() -> None:
    """Main entry point for T030c."""
    config = get_config()
    output_path = Path(config["paths"]["data_processed"]) / "mdc_stats.json"
    
    logger.info("Starting MDC statistics computation (T030c)...")
    
    try:
        df = load_retrieval_results(config)
        stats = compute_mdc_statistics(df)
        save_mdc_stats(stats, output_path)
        logger.info("T030c completed successfully.")
    except FileNotFoundError as e:
        logger.error(f"Data dependency missing: {e}")
        raise
    except ValueError as e:
        logger.error(f"Data validation error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during MDC statistics computation: {e}")
        raise

if __name__ == "__main__":
    main()