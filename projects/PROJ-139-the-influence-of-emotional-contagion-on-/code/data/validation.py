import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd

from code.config.settings import get_config
from code.utils.logging_config import get_logger

# Constants
VALIDITY_THRESHOLD = 0.30  # 30%
FAILURE_REASON_CODE = "SC-006_LOW_VALIDITY"
FAILURE_REASON_MESSAGE = "The proportion of valid threads (with ground truth) is below the required 30% threshold, failing study constraint SC-006."

# Setup logging
logger = get_logger(__name__)

def load_processed_data() -> pd.DataFrame:
    """
    Load the processed dataset containing thread metrics and sentiment analysis.
    Expected path: data/processed/threads_metrics.csv (or similar processed file)
    """
    config = get_config()
    # Assuming the output from T019 (validate_and_classify) is the source for this check
    # The task T019 produces 'data/processed/valid_threads.csv'
    input_path = config.dataset_paths.processed_dir / "valid_threads.csv"
    
    if not input_path.exists():
        # Fallback to the raw processed metrics if the classified file doesn't exist yet,
        # though T019 should have run first.
        input_path = config.dataset_paths.processed_dir / "threads_metrics.csv"
        
    if not input_path.exists():
        raise FileNotFoundError(f"Processed data file not found at {input_path}")
    
    logger.info(f"Loading processed data from {input_path}")
    return pd.read_csv(input_path)

def check_ground_truth_availability(row: pd.Series) -> bool:
    """
    Check if a specific thread has valid ground truth data.
    Criteria: 'ground_truth_label' and 'ground_truth_source' must exist and be non-null.
    """
    try:
        has_label = pd.notna(row.get('ground_truth_label'))
        has_source = pd.notna(row.get('ground_truth_source'))
        return bool(has_label and has_source)
    except Exception as e:
        logger.warning(f"Error checking ground truth for row: {e}")
        return False

def classify_thread(row: pd.Series) -> Tuple[str, Optional[str]]:
    """
    Classify a thread as 'valid' or 'excluded' based on ground truth availability.
    Returns: (status, reason_code)
    """
    if check_ground_truth_availability(row):
        return "valid", None
    else:
        reason = "MISSING_GROUND_TRUTH"
        if pd.isna(row.get('ground_truth_label')):
            reason = "MISSING_LABEL"
        elif pd.isna(row.get('ground_truth_source')):
            reason = "MISSING_SOURCE"
        return "excluded", reason

def validate_and_classify(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply classification to the entire dataframe.
    Updates the dataframe with 'classification_status' and 'exclusion_reason' columns.
    """
    logger.info(f"Classifying {len(df)} threads based on ground truth availability.")
    
    results = df.apply(classify_thread, axis=1)
    df['classification_status'] = results.apply(lambda x: x[0])
    df['exclusion_reason'] = results.apply(lambda x: x[1])
    
    valid_count = (df['classification_status'] == 'valid').sum()
    total_count = len(df)
    percentage = (valid_count / total_count * 100) if total_count > 0 else 0.0
    
    logger.info(f"Classification complete: {valid_count}/{total_count} ({percentage:.2f}%) are valid.")
    return df

def save_validated_dataset(df: pd.DataFrame, output_path: Optional[Path] = None) -> None:
    """
    Save the classified dataset to CSV.
    """
    config = get_config()
    if output_path is None:
        output_path = config.dataset_paths.processed_dir / "valid_threads.csv"
    
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    df.to_csv(output_path, index=False)
    logger.info(f"Saved validated dataset to {output_path}")

def generate_failure_report(valid_percentage: float, total_threads: int, valid_threads: int, output_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Generate the formal failure report for SC-006 if valid threads < 30%.
    This is the core logic for T019b.
    """
    config = get_config()
    if output_path is None:
        output_path = config.dataset_paths.processed_dir / "validity_failure_report.json"
    
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    report = {
        "study_id": "PROJ-139-the-influence-of-emotional-contagion-on-",
        "constraint_id": "SC-006",
        "constraint_description": "Minimum 30% of threads must have valid ground truth data.",
        "status": "FAILED" if valid_percentage < (VALIDITY_THRESHOLD * 100) else "PASSED",
        "threshold_percentage": VALIDITY_THRESHOLD * 100,
        "actual_percentage": valid_percentage,
        "total_threads_analyzed": total_threads,
        "valid_threads_count": valid_threads,
        "excluded_threads_count": total_threads - valid_threads,
        "reason": FAILURE_REASON_MESSAGE if valid_percentage < (VALIDITY_THRESHOLD * 100) else "Threshold met.",
        "timestamp": pd.Timestamp.now().isoformat()
    }
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Generated failure report at {output_path}: Status={report['status']}")
    return report

def run_validation_pipeline() -> Dict[str, Any]:
    """
    Main pipeline function for T019 and T019b.
    1. Load processed data.
    2. Classify threads.
    3. Save valid threads.
    4. Check threshold and generate failure report if necessary.
    """
    try:
        df = load_processed_data()
        df_classified = validate_and_classify(df)
        save_validated_dataset(df_classified)
        
        valid_count = (df_classified['classification_status'] == 'valid').sum()
        total_count = len(df_classified)
        valid_percentage = (valid_count / total_count * 100) if total_count > 0 else 0.0
        
        report = generate_failure_report(valid_percentage, total_count, valid_count)
        
        return report
        
    except Exception as e:
        logger.error(f"Validation pipeline failed: {e}")
        raise

def main():
    """
    Entry point for running the validation pipeline as a script.
    """
    logging.basicConfig(level=logging.INFO)
    logger.info("Starting Validation Pipeline (T019/T019b)...")
    
    try:
        result = run_validation_pipeline()
        logger.info(f"Pipeline completed. Status: {result['status']}")
        if result['status'] == 'FAILED':
            logger.warning(f"Study Constraint SC-006 FAILED. Valid threads: {result['actual_percentage']:.2f}% (Threshold: {result['threshold_percentage']}%)")
        else:
            logger.info("Study Constraint SC-006 PASSED.")
    except Exception as e:
        logger.error(f"Pipeline execution failed with error: {e}")
        raise

if __name__ == "__main__":
    main()