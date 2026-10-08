import os
import json
import logging
import pandas as pd
from pathlib import Path
from typing import Tuple, List, Optional

from utils.logging import setup_logger

logger = setup_logger(__name__)

# Required columns for behavioral validation as per T002/T003 spec
REQUIRED_BEHAVIORAL_COLUMNS = [
    'pre_motor_score',
    'post_motor_score',
    'age',
    'sex',
    'subject_id'
]

def load_retention_metrics(input_path: str) -> pd.DataFrame:
    """
    Load the downloaded metadata from the specified path.
    
    Args:
        input_path: Path to the metadata CSV file.
        
    Returns:
        DataFrame containing the metadata.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        pd.errors.EmptyDataError: If the file is empty.
    """
    logger.info(f"Loading retention metrics from {input_path}")
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Metadata file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} rows from metadata")
    return df

def load_behavioral_data(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
    """
    Identify subjects with valid behavioral data.
    A subject is valid if they have non-null values for all required behavioral columns.
    
    Args:
        df: The full metadata DataFrame.
        
    Returns:
        Tuple of (valid_df, list_of_excluded_subject_ids)
    """
    # Check for required columns first
    missing_cols = [col for col in REQUIRED_BEHAVIORAL_COLUMNS if col not in df.columns]
    if missing_cols:
        # This case should ideally be caught by T002, but we enforce it here too
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    # Identify rows with valid data (no NaN in required columns)
    valid_mask = df[REQUIRED_BEHAVIORAL_COLUMNS].notna().all(axis=1)
    valid_df = df[valid_mask].copy()
    
    excluded_subjects = df[~valid_mask]['subject_id'].tolist()
    
    logger.info(f"Valid subjects: {len(valid_df)}, Excluded subjects: {len(excluded_subjects)}")
    return valid_df, excluded_subjects

def validate_retention_threshold(
    total_subjects: int, 
    retained_subjects: int, 
    threshold: float = 0.80
) -> Tuple[bool, str]:
    """
    Validate if the retention rate meets the specified threshold.
    
    Args:
        total_subjects: Total number of subjects in the dataset.
        retained_subjects: Number of subjects with valid behavioral data.
        threshold: Minimum retention rate required (default 0.80).
        
    Returns:
        Tuple of (passes_threshold, reason_string)
    """
    if total_subjects == 0:
        return False, "Total subjects is zero"
        
    retention_rate = retained_subjects / total_subjects
    logger.info(f"Retention rate: {retention_rate:.4f} ({retained_subjects}/{total_subjects})")
    
    if retention_rate < threshold:
        return False, f"Retention rate {retention_rate:.4f} is below threshold {threshold}"
        
    return True, "Retention threshold met"

def save_retention_metrics(
    output_path: str, 
    retention_rate: float, 
    total_subjects: int, 
    retained_subjects: int,
    excluded_reasons: Optional[dict] = None
) -> None:
    """
    Save retention metrics to a JSON file.
    
    Args:
        output_path: Path to the output JSON file.
        retention_rate: Calculated retention rate.
        total_subjects: Total number of subjects.
        retained_subjects: Number of retained subjects.
        excluded_reasons: Optional dictionary of exclusion reasons.
    """
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        
    metrics = {
        "retention_rate": retention_rate,
        "total_subjects": total_subjects,
        "retained_subjects": retained_subjects,
        "threshold": 0.80,
        "status": "passed" if retention_rate >= 0.80 else "failed"
    }
    
    if excluded_reasons:
        metrics["excluded_reasons"] = excluded_reasons
        
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)
        
    logger.info(f"Saved retention metrics to {output_path}")

def run_retention_validation(
    input_path: str,
    output_path: str,
    threshold: float = 0.80
) -> bool:
    """
    Main execution function for retention validation.
    
    This function:
    1. Loads the metadata CSV.
    2. Validates the presence of required columns.
    3. Calculates retention rate (subjects with valid data / total).
    4. If retention < 80%, logs a fatal error and exits.
    5. Saves retention metrics to JSON.
    
    Args:
        input_path: Path to input metadata CSV.
        output_path: Path to output retention metrics JSON.
        threshold: Minimum retention rate (default 0.80).
        
    Returns:
        True if validation passes, False if it fails (fatal exit).
    """
    try:
        # Load data
        df = load_retention_metrics(input_path)
        
        # Validate columns (T002 check)
        missing_cols = [col for col in REQUIRED_BEHAVIORAL_COLUMNS if col not in df.columns]
        if missing_cols:
            fatal_msg = f"Fatal: Dataset lacks behavioral motor task metrics. Missing columns: {missing_cols}"
            logger.error(fatal_msg)
            # Exit immediately as per T002/T003 spec
            raise SystemExit(fatal_msg)
        
        # Calculate retention
        valid_df, excluded_subjects = load_behavioral_data(df)
        total_subjects = len(df)
        retained_subjects = len(valid_df)
        
        # Validate threshold
        passes, reason = validate_retention_threshold(total_subjects, retained_subjects, threshold)
        
        if not passes:
            # Determine if missing data or motion artifacts (simplified here to missing data)
            # In a real scenario, we'd check specific columns for motion artifacts
            fatal_msg = f"Fatal: Retention < 80% due to missing behavioral data ({reason})"
            logger.error(fatal_msg)
            raise SystemExit(fatal_msg)
        
        # Save metrics
        retention_rate = retained_subjects / total_subjects
        save_retention_metrics(output_path, retention_rate, total_subjects, retained_subjects)
        
        logger.info(f"Retention validation PASSED. Rate: {retention_rate:.4f}")
        return True
        
    except SystemExit:
        raise
    except Exception as e:
        logger.error(f"Retention validation failed with exception: {e}")
        raise

def main():
    """Entry point for the script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate retention rates from metadata.")
    parser.add_argument("--input", type=str, required=True, help="Path to input metadata CSV")
    parser.add_argument("--output", type=str, required=True, help="Path to output retention metrics JSON")
    parser.add_argument("--threshold", type=float, default=0.80, help="Minimum retention rate threshold")
    
    args = parser.parse_args()
    
    run_retention_validation(args.input, args.output, args.threshold)

if __name__ == "__main__":
    main()
