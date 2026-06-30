import os
import sys
import logging
import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Optional

from main import load_config
from contracts import validate_csv_file, validate_record

logger = logging.getLogger(__name__)

def load_flags(filepath: str) -> pd.DataFrame:
    """Load the flags.csv file produced by the MMD detector."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Flags file not found: {filepath}")
    df = pd.read_csv(filepath)
    # Ensure week column is numeric for comparison
    if 'week' in df.columns:
        df['week'] = pd.to_numeric(df['week'], errors='coerce')
    return df

def load_ground_truth(filepath: str) -> pd.DataFrame:
    """Load the ground truth events CSV."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Ground truth file not found: {filepath}")
    df = pd.read_csv(filepath)
    # Ensure start_week is numeric
    if 'start_week' in df.columns:
        df['start_week'] = pd.to_numeric(df['start_week'], errors='coerce')
    return df

def calculate_detection_delay(flagged_week: float, true_start_week: float, tolerance: int = 2) -> Optional[float]:
    """
    Calculate the detection delay for a single true event.
    Returns the delay (flagged_week - true_start_week) if the flag is within tolerance.
    Returns None if no flag is within tolerance.
    """
    diff = flagged_week - true_start_week
    if abs(diff) <= tolerance:
        return diff
    return None

def compute_metrics(
    flags_df: pd.DataFrame,
    truth_df: pd.DataFrame,
    tolerance: int = 2
) -> Dict[str, float]:
    """
    Compute Precision, Recall, and average Detection Delay.

    Precision: TP / (TP + FP)
    Recall: TP / (TP + FN)
    Detection Delay: Average of (flagged_week - true_start_week) for all matched pairs.

    Matching logic:
    - A True Event is "detected" if there exists at least one flagged week within [start_week - tolerance, start_week + tolerance].
    - A Flagged Week is a "True Positive" if it falls within tolerance of ANY true event start.
    - A Flagged Week is a "False Positive" if it does not fall within tolerance of ANY true event.
    - A True Event is a "False Negative" if NO flagged week falls within its tolerance window.
    """
    true_events = truth_df['start_week'].dropna().unique()
    flagged_weeks = flags_df['week'].dropna().unique()

    true_positives = 0
    false_positives = 0
    delays = []

    # Track which true events have been detected
    detected_events = set()

    # 1. Identify True Positives and calculate delays
    for flag_week in flagged_weeks:
        is_tp = False
        for true_week in true_events:
            if abs(flag_week - true_week) <= tolerance:
                is_tp = True
                detected_events.add(true_week)
                # Calculate delay for this specific match
                delay = flag_week - true_week
                delays.append(delay)
                break # A flag only needs to match one event to be a TP
        
        if is_tp:
            true_positives += 1
        else:
            false_positives += 1

    # 2. Count False Negatives (True events not detected)
    false_negatives = len(true_events) - len(detected_events)

    # 3. Calculate Metrics
    precision = 0.0
    if (true_positives + false_positives) > 0:
        precision = true_positives / (true_positives + false_positives)

    recall = 0.0
    if (true_positives + false_negatives) > 0:
        recall = true_positives / (true_positives + false_negatives)

    avg_delay = 0.0
    if len(delays) > 0:
        avg_delay = float(np.mean(delays))

    return {
        "precision": precision,
        "recall": recall,
        "detection_delay": avg_delay,
        "true_positives": true_positives,
        "false_positives": false_positives,
        "false_negatives": false_negatives,
        "total_events": len(true_events),
        "total_flags": len(flagged_weeks)
    }

def evaluate_pipeline(
    flags_path: str,
    truth_path: str,
    output_path: str,
    tolerance: int = 2
) -> Dict[str, float]:
    """
    Main entry point for evaluation.
    Loads data, computes metrics, and saves a summary CSV.
    """
    logger.info(f"Loading flags from {flags_path}")
    flags_df = load_flags(flags_path)
    
    logger.info(f"Loading ground truth from {truth_path}")
    truth_df = load_ground_truth(truth_path)

    # Basic validation
    if 'week' not in flags_df.columns:
        raise ValueError("Flags file must contain a 'week' column")
    if 'start_week' not in truth_df.columns:
        raise ValueError("Ground truth file must contain a 'start_week' column")

    metrics = compute_metrics(flags_df, truth_df, tolerance=tolerance)

    # Save metrics to CSV
    metrics_df = pd.DataFrame([metrics])
    metrics_df.to_csv(output_path, index=False)
    logger.info(f"Metrics saved to {output_path}")
    
    return metrics

def main():
    """CLI entry point for evaluation."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    config = load_config()
    
    # Default paths based on project structure
    flags_path = "data/processed/flags.csv"
    truth_path = "data/raw/ground_truth_events.csv"
    output_path = "data/processed/evaluation_metrics.csv"
    
    # Allow override via config if present
    tolerance = config.get("tolerance", 2)

    try:
        metrics = evaluate_pipeline(flags_path, truth_path, output_path, tolerance=tolerance)
        print(f"Evaluation Complete:")
        print(f"  Precision: {metrics['precision']:.4f}")
        print(f"  Recall:    {metrics['recall']:.4f}")
        print(f"  Avg Delay: {metrics['detection_delay']:.2f} weeks")
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()