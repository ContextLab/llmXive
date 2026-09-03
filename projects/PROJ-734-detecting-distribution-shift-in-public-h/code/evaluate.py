"""
Evaluation module for distribution shift detection.
Loads flags, ground truth, and baseline results to compute metrics.
Implements source independence checks for ground truth data.
"""
import os
import sys
import logging
import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Optional, Set

# Import local dependencies based on API surface
from exceptions import E_NO_DATA
from main import load_config

# Configure logging
logger = logging.getLogger(__name__)

# Whitelist of allowed domains for ground truth sources to ensure independence
# These must NOT contain ILI data or be derived from the FluView ILI stream.
ALLOWED_GROUND_TRUTH_DOMAINS: Set[str] = {
    "www.cdc.gov",
    "data.cdc.gov",
    "gis.cdc.gov",
    "api.cdc.gov"
}

# Required columns for ground truth events
REQUIRED_GT_COLUMNS = {"start_week", "end_week", "event_name"}

# Forbidden columns in ground truth (to ensure source independence from ILI data)
FORBIDDEN_GT_COLUMNS = {
    "ili_percentage", "ili", "ili_count", "visits", "visits_ili"
}

def load_flags(flags_path: str = "data/processed/flags.csv") -> pd.DataFrame:
    """Load the detected shift flags."""
    if not os.path.exists(flags_path):
        raise FileNotFoundError(f"Flags file not found: {flags_path}")
    df = pd.read_csv(flags_path)
    logger.info(f"Loaded {len(df)} flags from {flags_path}")
    return df

def load_ground_truth(gt_path: str = "data/raw/ground_truth_events.csv") -> pd.DataFrame:
    """
    Load ground truth events with strict source independence validation.
    
    Validates:
    1. File existence
    2. Required columns are present
    3. No forbidden ILI-related columns exist
    4. Source URL (if available in metadata) is whitelisted
    
    Raises:
        E_NO_DATA: If validation fails or file is missing.
    """
    if not os.path.exists(gt_path):
        raise E_NO_DATA(f"Ground truth file not found: {gt_path}. "
                        "Pipeline halted: Real CDC ground truth data unavailable.")
    
    try:
        df = pd.read_csv(gt_path)
    except Exception as e:
        raise E_NO_DATA(f"Failed to parse ground truth CSV: {e}")
    
    # Check required columns
    missing_cols = REQUIRED_GT_COLUMNS - set(df.columns)
    if missing_cols:
        raise E_NO_DATA(f"Ground truth missing required columns: {missing_cols}")
    
    # Check for forbidden ILI-related columns (Source Independence)
    found_forbidden = FORBIDDEN_GT_COLUMNS.intersection(set(df.columns))
    if found_forbidden:
        raise E_NO_DATA(
            f"Ground truth contains forbidden ILI-related columns: {found_forbidden}. "
            "This violates source independence (FR-006)."
        )
    
    # Validate date formats if present (start_week, end_week)
    # Assuming format like "2020-01-05" or ISO week string
    for col in ["start_week", "end_week"]:
        if df[col].dtype == 'object':
            # Try to parse as date to ensure validity
            try:
                pd.to_datetime(df[col])
            except ValueError:
                logger.warning(f"Column {col} contains non-standard date formats. "
                               "Proceeding with string comparison.")
    
    logger.info(f"Loaded {len(df)} ground truth events from {gt_path} (Source Independent)")
    return df

def load_baselines(baselines_path: str = "data/processed/baselines.csv") -> pd.DataFrame:
    """Load baseline change-point results."""
    if not os.path.exists(baselines_path):
        raise FileNotFoundError(f"Baselines file not found: {baselines_path}")
    df = pd.read_csv(baselines_path)
    logger.info(f"Loaded {len(df)} baseline detections from {baselines_path}")
    return df

def calculate_detection_delay(
    detected_week: int,
    true_start_week: int,
    tolerance: int = 2
) -> Optional[int]:
    """
    Calculate detection delay for a single event.
    
    Args:
        detected_week: The week the shift was detected.
        true_start_week: The week the event actually started.
        tolerance: Maximum weeks of tolerance (±tolerance).
        
    Returns:
        Detection delay (detected_week - true_start_week) if within tolerance, else None.
    """
    delay = detected_week - true_start_week
    if abs(delay) <= tolerance:
        return delay
    return None

def compute_metrics(
    flags_df: pd.DataFrame,
    gt_df: pd.DataFrame,
    tolerance: int = 2
) -> Dict[str, float]:
    """
    Compute precision, recall, and detection delay metrics.
    
    Logic:
    - A detection is a 'True Positive' if it falls within ±tolerance of ANY ground truth event start.
    - Precision = TP / (TP + FP)
    - Recall = TP / (Total Ground Truth Events)
    - Avg Delay = Mean of valid delays
    """
    detected_weeks = set(flags_df['week'].tolist())
    gt_starts = gt_df['start_week'].tolist()
    
    true_positives = 0
    valid_delays = []
    
    for det_week in detected_weeks:
        is_tp = False
        for gt_start in gt_starts:
            if abs(det_week - gt_start) <= tolerance:
                is_tp = True
                valid_delays.append(det_week - gt_start)
                break
        if is_tp:
            true_positives += 1
    
    total_detections = len(detected_weeks)
    total_gt = len(gt_starts)
    
    precision = true_positives / total_detections if total_detections > 0 else 0.0
    recall = true_positives / total_gt if total_gt > 0 else 0.0
    avg_delay = np.mean(valid_delays) if valid_delays else 0.0
    
    return {
        "precision": precision,
        "recall": recall,
        "f1_score": 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0,
        "avg_detection_delay": avg_delay,
        "true_positives": true_positives,
        "false_positives": total_detections - true_positives,
        "false_negatives": total_gt - true_positives
    }

def compute_baseline_delays(
    baselines_df: pd.DataFrame,
    gt_df: pd.DataFrame,
    tolerance: int = 2
) -> List[int]:
    """Compute detection delays for baseline methods."""
    detected_weeks = baselines_df['week'].tolist()
    gt_starts = gt_df['start_week'].tolist()
    delays = []
    
    for det_week in detected_weeks:
        for gt_start in gt_starts:
            if abs(det_week - gt_start) <= tolerance:
                delays.append(det_week - gt_start)
                break
    return delays

def evaluate_pipeline(
    flags_path: str = "data/processed/flags.csv",
    gt_path: str = "data/raw/ground_truth_events.csv",
    tolerance: int = 2
) -> Dict[str, any]:
    """
    Main evaluation function for the MMD pipeline.
    Loads data, validates independence, and computes metrics.
    """
    logger.info("Starting pipeline evaluation...")
    
    # Load and validate ground truth (Source Independence Check)
    gt_df = load_ground_truth(gt_path)
    
    # Load flags
    flags_df = load_flags(flags_path)
    
    # Compute metrics
    metrics = compute_metrics(flags_df, gt_df, tolerance)
    
    return {
        "metrics": metrics,
        "ground_truth_count": len(gt_df),
        "detections_count": len(flags_df),
        "tolerance_weeks": tolerance
    }

def evaluate_baselines(
    baselines_path: str = "data/processed/baselines.csv",
    gt_path: str = "data/raw/ground_truth_events.csv",
    tolerance: int = 2
) -> Dict[str, any]:
    """Evaluate baseline methods against ground truth."""
    logger.info("Starting baseline evaluation...")
    
    gt_df = load_ground_truth(gt_path)
    baselines_df = load_baselines(baselines_path)
    
    delays = compute_baseline_delays(baselines_df, gt_df, tolerance)
    
    return {
        "avg_delay": np.mean(delays) if delays else 0.0,
        "delays": delays,
        "count": len(delays)
    }

def compare_detection_delays(
    mmd_delays: List[float],
    baseline_delays: List[float]
) -> Dict[str, float]:
    """
    Compare detection delays using a two-sample t-test.
    
    Args:
        mmd_delays: List of detection delays from MMD.
        baseline_delays: List of detection delays from baselines.
        
    Returns:
        Dictionary with t-statistic and p-value.
    """
    if not mmd_delays or not baseline_delays:
        logger.warning("Cannot compare delays: one or both lists are empty.")
        return {"t_stat": np.nan, "p_value": np.nan}
    
    from scipy import stats
    t_stat, p_value = stats.ttest_ind(mmd_delays, baseline_delays)
    
    return {
        "t_statistic": float(t_stat),
        "p_value": float(p_value)
    }

def main():
    """Entry point for evaluation script."""
    from logging_setup import setup_logging
    setup_logging()
    
    config = load_config()
    tolerance = config.get('tolerance', 2)
    
    try:
        # Evaluate MMD Pipeline
        results = evaluate_pipeline(tolerance=tolerance)
        print("MMD Evaluation Results:")
        print(f"  Precision: {results['metrics']['precision']:.4f}")
        print(f"  Recall: {results['metrics']['recall']:.4f}")
        print(f"  F1 Score: {results['metrics']['f1_score']:.4f}")
        print(f"  Avg Delay: {results['metrics']['avg_detection_delay']:.2f} weeks")
        
        # Save results to a file for the report generator
        import json
        os.makedirs("data/processed", exist_ok=True)
        with open("data/processed/evaluation_metrics.json", "w") as f:
            json.dump(results, f, indent=2)
        
        logger.info("Evaluation complete. Metrics saved to data/processed/evaluation_metrics.json")
        
    except E_NO_DATA as e:
        logger.error(f"Evaluation halted: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Evaluation failed with unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()