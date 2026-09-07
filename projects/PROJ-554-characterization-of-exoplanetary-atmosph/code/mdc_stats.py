"""
Module to compute and save Minimum Detectable Concentration (MDC) statistics.

This module aggregates MDC values derived from retrieval results to determine
the global sensitivity floor of the study, addressing reviewer concerns about
detection limits and evidentiary standards.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List

import pandas as pd
import numpy as np

# Import from existing project modules
from config import get_config

# Configure logging
logger = logging.getLogger(__name__)

def load_retrieval_results(input_path: Optional[str] = None) -> pd.DataFrame:
    """
    Load retrieval results from CSV file.
    
    Args:
        input_path: Path to retrieval results CSV. If None, uses config default.
        
    Returns:
        DataFrame containing retrieval results with MDC columns.
        
    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If required columns are missing.
    """
    config = get_config()
    if input_path is None:
        input_path = str(config.processed_dir / "retrieval_results.csv")
        
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Retrieval results file not found: {input_path}")
        
    df = pd.read_csv(path)
    
    required_cols = ["min_detectable_concentration", "is_upper_limit"]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in retrieval results: {missing_cols}")
        
    logger.info(f"Loaded {len(df)} retrieval results from {input_path}")
    return df

def compute_mdc_statistics(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Compute aggregate statistics for Minimum Detectable Concentration (MDC).
    
    This function calculates global sensitivity metrics addressing reviewer
    demands for detection limit definitions (Marie Curie, Rosalind Franklin).
    
    Args:
        df: DataFrame with 'min_detectable_concentration' and 'is_upper_limit' columns.
        
    Returns:
        Dictionary containing MDC statistics.
    """
    if df.empty:
        logger.warning("Empty DataFrame provided for MDC statistics computation")
        return {
            "count": 0,
            "global_95th_percentile_mdc": None,
            "global_median_mdc": None,
            "global_min_mdc": None,
            "global_max_mdc": None,
            "upper_limit_count": 0,
            "detection_count": 0,
            "sample_coverage": "N/A (no data)"
        }
    
    mdc_values = df["min_detectable_concentration"].dropna()
    
    if mdc_values.empty:
        logger.warning("No valid MDC values found in dataset")
        return {
            "count": len(df),
            "global_95th_percentile_mdc": None,
            "global_median_mdc": None,
            "global_min_mdc": None,
            "global_max_mdc": None,
            "upper_limit_count": int(df["is_upper_limit"].sum()),
            "detection_count": int(len(df) - df["is_upper_limit"].sum()),
            "sample_coverage": "N/A (no MDC values)"
        }
    
    # Calculate statistics
    count = len(mdc_values)
    median_mdc = float(mdc_values.median())
    min_mdc = float(mdc_values.min())
    max_mdc = float(mdc_values.max())
    p95_mdc = float(mdc_values.quantile(0.95))
    
    # Count upper limits vs detections
    upper_limit_count = int(df["is_upper_limit"].sum())
    detection_count = int(len(df) - upper_limit_count)
    
    # Determine sample coverage description
    if count > 0:
        coverage_pct = (detection_count / count) * 100
        sample_coverage = f"{coverage_pct:.1f}% detections ({detection_count}/{count})"
    else:
        sample_coverage = "0% detections (0/0)"
    
    stats = {
        "count": count,
        "global_95th_percentile_mdc": p95_mdc,
        "global_median_mdc": median_mdc,
        "global_min_mdc": min_mdc,
        "global_max_mdc": max_mdc,
        "upper_limit_count": upper_limit_count,
        "detection_count": detection_count,
        "sample_coverage": sample_coverage,
        "units": "mixing_ratio_log10"
    }
    
    logger.info(f"Computed MDC statistics: median={median_mdc:.4f}, 95th_pctl={p95_mdc:.4f}")
    return stats

def save_mdc_stats(stats: Dict[str, Any], output_path: Optional[str] = None) -> str:
    """
    Save MDC statistics to JSON file.
    
    Args:
        stats: Dictionary of MDC statistics.
        output_path: Path for output JSON. If None, uses config default.
        
    Returns:
        Path to saved file.
    """
    config = get_config()
    if output_path is None:
        output_path = str(config.processed_dir / "mdc_stats.json")
        
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)
        
    logger.info(f"Saved MDC statistics to {output_path}")
    return output_path

def main() -> int:
    """
    Main entry point for MDC statistics computation.
    
    Returns:
        Exit code (0 for success, 1 for failure).
    """
    try:
        # Load configuration
        config = get_config()
        logger.info("Starting MDC statistics computation")
        
        # Load retrieval results
        input_path = config.processed_dir / "retrieval_results.csv"
        df = load_retrieval_results(str(input_path))
        
        # Compute statistics
        stats = compute_mdc_statistics(df)
        
        # Save results
        output_path = config.processed_dir / "mdc_stats.json"
        save_mdc_stats(stats, str(output_path))
        
        logger.info("MDC statistics computation completed successfully")
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Value error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during MDC statistics computation: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())