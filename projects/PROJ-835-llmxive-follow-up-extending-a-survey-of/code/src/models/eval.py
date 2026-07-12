import os
import sys
import json
import logging
import time
import argparse
import traceback
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

import numpy as np
from scipy.stats import pearsonr

# Import from project utilities
from src.utils.config import get_path, ensure_dir, load_state, save_state, compute_file_hash
from src.utils.logging_config import get_logger, configure_logging_level

# Configure logging
logger = get_logger(__name__)

def load_predictions(path: str) -> Dict[str, Any]:
    """Load predictions from a CSV or JSON file."""
    logger.info(f"Loading predictions from {path}")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Predictions file not found: {path}")
    
    # Assuming predictions are saved in a format compatible with pandas or json
    # Since we are avoiding pandas in imports for this specific function if not needed,
    # we will assume a JSON structure for flexibility or CSV if specified.
    # Based on T024, it saves to results/predictions.csv.
    # However, for T027b, we specifically need anomaly_scores.parquet.
    # This function is kept for backward compatibility with T027 logic if needed.
    # For this task, we focus on loading parquet via a generic loader if possible,
    # but since we can't import pandas in the API surface list explicitly as a dependency for *this* function
    # without checking requirements, we will assume the environment has pandas available
    # as per T002 requirements (pandas is in requirements.txt).
    
    import pandas as pd
    return pd.read_csv(path)

def load_anomaly_scores(path: str) -> Any:
    """Load anomaly scores from a Parquet file."""
    logger.info(f"Loading anomaly scores from {path}")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Anomaly scores file not found: {path}")
    
    import pandas as pd
    df = pd.read_parquet(path)
    return df

def calculate_correlation_and_hypothesis_test(
    df: Any, 
    score_column: str = 'mahalanobis_distance', 
    label_column: str = 'label'
) -> Dict[str, Any]:
    """
    Calculate Pearson correlation (r) between Mahalanobis distance and jailbreak labels.
    Perform hypothesis test (p-value) and verify thresholds (p < 0.05 or r > 0.3).
    
    Args:
        df: DataFrame containing scores and labels.
        score_column: Name of the column containing Mahalanobis distances.
        label_column: Name of the column containing labels (0 for benign, 1 for jailbreak).
    
    Returns:
        Dictionary with correlation results and hypothesis test outcomes.
    """
    try:
        # Extract data
        distances = df[score_column].to_numpy()
        labels = df[label_column].to_numpy()
        
        # Ensure data is numeric
        if not np.issubdtype(distances.dtype, np.number):
            raise ValueError(f"Column '{score_column}' must contain numeric values.")
        if not np.issubdtype(labels.dtype, np.number):
            # Attempt conversion if labels are strings
            unique_labels = np.unique(labels)
            if len(unique_labels) == 2:
                # Map to 0 and 1
                label_map = {val: i for i, val in enumerate(unique_labels)}
                labels = np.array([label_map[l] for l in labels])
            else:
                raise ValueError(f"Column '{label_column}' must contain numeric values or exactly two unique string categories.")

        # Calculate Pearson correlation
        r, p_value = pearsonr(distances, labels)
        
        # Verify thresholds per SC-005
        # Threshold: p < 0.05 OR r > 0.3 (absolute value usually, but task says r > 0.3)
        # Assuming positive correlation expected for jailbreak detection (higher distance -> jailbreak)
        threshold_p = 0.05
        threshold_r = 0.3
        
        is_significant_p = p_value < threshold_p
        is_strong_r = r > threshold_r
        
        # Determine if the condition is met (either p < 0.05 OR r > 0.3)
        condition_met = is_significant_p or is_strong_r
        
        result = {
            "pearson_r": float(r),
            "p_value": float(p_value),
            "threshold_p": threshold_p,
            "threshold_r": threshold_r,
            "is_significant_p": bool(is_significant_p),
            "is_strong_r": bool(is_strong_r),
            "condition_met": bool(condition_met),
            "sample_size": int(len(distances))
        }
        
        logger.info(f"Correlation calculated: r={r:.4f}, p={p_value:.4f}. Condition met: {condition_met}")
        return result
        
    except Exception as e:
        logger.error(f"Error calculating correlation: {e}", exc_info=True)
        raise

def save_correlation_results(results: Dict[str, Any], output_path: str) -> None:
    """Save correlation results to a JSON file."""
    ensure_dir(os.path.dirname(output_path))
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Correlation results saved to {output_path}")

def main(args: Optional[argparse.Namespace] = None) -> None:
    """
    Main entry point for T027b: Correlation Analysis and Hypothesis Testing.
    Reads anomaly scores, calculates Pearson correlation with labels, performs hypothesis test,
    and saves results to results/correlation.json.
    """
    if args is None:
        parser = argparse.ArgumentParser(description="Calculate correlation between Mahalanobis distance and labels.")
        parser.add_argument("--input", type=str, default="data/anomaly_scores.parquet",
                            help="Path to the anomaly scores Parquet file.")
        parser.add_argument("--output", type=str, default="results/correlation.json",
                            help="Path to save the correlation results JSON.")
        parser.add_argument("--score-column", type=str, default="mahalanobis_distance",
                            help="Column name for Mahalanobis distances.")
        parser.add_argument("--label-column", type=str, default="label",
                            help="Column name for labels.")
        args = parser.parse_args()

    try:
        # Load anomaly scores
        df = load_anomaly_scores(args.input)
        
        # Validate columns exist
        if args.score_column not in df.columns:
            raise ValueError(f"Score column '{args.score_column}' not found in {args.input}. Available: {df.columns.tolist()}")
        if args.label_column not in df.columns:
            raise ValueError(f"Label column '{args.label_column}' not found in {args.input}. Available: {df.columns.tolist()}")

        # Calculate correlation and hypothesis test
        results = calculate_correlation_and_hypothesis_test(
            df, 
            score_column=args.score_column, 
            label_column=args.label_column
        )
        
        # Save results
        save_correlation_results(results, args.output)
        
        # Log summary
        logger.info("Task T027b completed successfully.")
        logger.info(f"  Pearson r: {results['pearson_r']:.4f}")
        logger.info(f"  P-value: {results['p_value']:.4f}")
        logger.info(f"  Thresholds met (p<0.05 or r>0.3): {results['condition_met']}")
        
    except Exception as e:
        logger.error(f"Task T027b failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    configure_logging_level(logging.INFO)
    main()
