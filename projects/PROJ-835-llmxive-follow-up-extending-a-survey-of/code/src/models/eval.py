import os
import sys
import json
import logging
import time
import argparse
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

import numpy as np
import pandas as pd
from scipy.stats import pearsonr

# Import local utilities to ensure consistent logging and config
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.config import get_path, ensure_dir, load_state, save_state
from utils.logging_config import get_module_logger

# Ensure CPU-only mode is enforced
os.environ["CUDA_VISIBLE_DEVICES"] = ""

logger = get_module_logger(__name__)

def load_predictions(path: Path) -> pd.DataFrame:
    """
    Load predictions from a CSV file.
    Expected columns: ['sample_id', 'prediction', 'probability', 'label']
    """
    if not path.exists():
        raise FileNotFoundError(f"Predictions file not found: {path}")
    df = pd.read_csv(path)
    logger.info(f"Loaded {len(df)} predictions from {path}")
    return df

def load_anomaly_scores(path: Path) -> pd.DataFrame:
    """
    Load anomaly scores from a Parquet file.
    Expected columns: ['sample_id', 'mahalanobis_distance', 'label']
    """
    if not path.exists():
        raise FileNotFoundError(f"Anomaly scores file not found: {path}")
    df = pd.read_parquet(path)
    logger.info(f"Loaded {len(df)} anomaly scores from {path}")
    return df

def calculate_correlation_and_hypothesis_test(
    df: pd.DataFrame
) -> Tuple[float, float, Dict[str, Any]]:
    """
    Calculate Pearson correlation (r) between Mahalanobis distance and jailbreak labels.
    Perform a hypothesis test (p-value) for the correlation.

    Args:
        df: DataFrame containing 'mahalanobis_distance' and 'label' columns.

    Returns:
        Tuple of (correlation_coefficient, p_value, stats_dict)
    """
    # Ensure we have numeric data
    if 'mahalanobis_distance' not in df.columns or 'label' not in df.columns:
        raise ValueError(
            "DataFrame must contain 'mahalanobis_distance' and 'label' columns"
        )

    distances = df['mahalanobis_distance'].values
    labels = df['label'].values

    # Calculate Pearson correlation
    r, p_value = pearsonr(distances, labels)

    logger.info(f"Pearson Correlation (r): {r:.6f}")
    logger.info(f"P-value: {p_value:.6f}")

    # Determine if threshold is met (SC-005: p < 0.05 OR r > 0.3)
    # Note: The requirement says "p < 0.05 or r > 0.3".
    # Since r can be negative, we check the magnitude or the specific direction.
    # Typically, we expect positive correlation (jailbreaks have higher distances).
    # We will flag as "significant" if p < 0.05 OR (r > 0.3 and p < 0.05 is not strictly required if r is strong enough per spec).
    # Strict interpretation of spec: "verify threshold (p < 0.05 or r > 0.3)"
    is_significant = (p_value < 0.05) or (r > 0.3)

    stats_dict = {
        "correlation_coefficient": float(r),
        "p_value": float(p_value),
        "sample_size": int(len(df)),
        "threshold_met": bool(is_significant),
        "threshold_p": 0.05,
        "threshold_r": 0.3,
    }

    return r, p_value, stats_dict

def save_correlation_results(results: Dict[str, Any], output_path: Path) -> None:
    """
    Save correlation results to a JSON file.
    """
    ensure_dir(output_path.parent)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Saved correlation results to {output_path}")

def main():
    """
    Main entry point for T027b: Correlation Analysis.
    Reads anomaly scores, calculates Pearson correlation with labels,
    performs hypothesis test, and saves results.
    """
    start_time = time.time()

    # Setup argument parser
    parser = argparse.ArgumentParser(description="T027b: Correlation Analysis")
    parser.add_argument(
        "--scores-path",
        type=str,
        default="data/anomaly_scores.parquet",
        help="Path to the anomaly scores Parquet file"
    )
    parser.add_argument(
        "--output-path",
        type=str,
        default="results/correlation.json",
        help="Path to save the correlation results JSON"
    )
    args = parser.parse_args()

    scores_path = Path(args.scores_path)
    output_path = Path(args.output_path)

    logger.info("Starting T027b: Correlation Analysis")
    logger.info(f"Input: {scores_path}")
    logger.info(f"Output: {output_path}")

    try:
        # Load data
        logger.info("Loading anomaly scores...")
        df_scores = load_anomaly_scores(scores_path)

        # Calculate correlation and hypothesis test
        logger.info("Calculating Pearson correlation and hypothesis test...")
        r, p_value, stats = calculate_correlation_and_hypothesis_test(df_scores)

        # Add metadata
        stats["analysis_timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        stats["task_id"] = "T027b"
        stats["input_file"] = str(scores_path)

        # Save results
        logger.info("Saving results...")
        save_correlation_results(stats, output_path)

        elapsed = time.time() - start_time
        logger.info(f"T027b completed successfully in {elapsed:.2f} seconds.")
        logger.info(f"Correlation (r): {r:.4f}, P-value: {p_value:.4f}")
        logger.info(f"Threshold Met (p<0.05 or r>0.3): {stats['threshold_met']}")

        return 0

    except FileNotFoundError as e:
        logger.error(f"Data file not found: {e}")
        logger.error("Ensure that T022b has run and produced data/anomaly_scores.parquet")
        return 1
    except Exception as e:
        logger.error(f"Error during correlation analysis: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
