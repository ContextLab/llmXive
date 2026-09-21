import os
import logging
import pandas as pd
import json
from pathlib import Path
from typing import Tuple, Optional
from utils.logging import setup_logger

logger = logging.getLogger(__name__)

def validate_retention_and_behavioral_data(
    metadata_path: str,
    output_path: str,
    min_retention_rate: float = 0.80
) -> Tuple[bool, dict]:
    """
    T003: Retention & Behavioral Validation.
    
    Reads the downloaded metadata from `data/raw/metadata.csv`.
    Calculates retention rate (subjects with valid data / total subjects).
    
    Logic:
    1. Load metadata.
    2. Identify total subjects.
    3. Identify subjects with valid behavioral data (non-null pre/post motor scores).
    4. Identify subjects with missing data due to motion artifacts (if flagged in metadata).
    5. Calculate retention rate based on valid behavioral data.
    6. If retention < 80% due to missing behavioral data -> Fatal Exit.
    7. If retention < 80% due to motion artifacts -> Warning & Proceed.
    8. Save metrics to `data/processed/behavioral/retention_metrics.json`.
    
    Args:
        metadata_path: Path to data/raw/metadata.csv
        output_path: Path to data/processed/behavioral/retention_metrics.json
        min_retention_rate: Threshold (default 0.80)
        
    Returns:
        Tuple[bool, dict]: (success, metrics_dict)
    """
    logger.info(f"Starting retention validation for {metadata_path}")
    
    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    try:
        df = pd.read_csv(metadata_path)
    except FileNotFoundError:
        logger.error(f"Fatal: Metadata file not found at {metadata_path}")
        raise FileNotFoundError(f"Metadata file not found: {metadata_path}")
    except Exception as e:
        logger.error(f"Fatal: Error reading metadata file: {e}")
        raise e
    
    if df.empty:
        logger.error("Fatal: Metadata file is empty.")
        raise ValueError("Metadata file is empty.")
        
    total_subjects = len(df)
    logger.info(f"Total subjects found: {total_subjects}")
    
    # Check for required columns
    required_cols = ['pre_motor_score', 'post_motor_score', 'subject_id']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        logger.error(f"Fatal: Missing required columns: {missing_cols}")
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    # Determine valid behavioral data
    # A subject has valid behavioral data if pre_motor_score and post_motor_score are not null
    behavioral_valid_mask = df['pre_motor_score'].notna() & df['post_motor_score'].notna()
    subjects_with_valid_behavior = df[behavioral_valid_mask]
    count_valid_behavior = len(subjects_with_valid_behavior)
    
    # Determine missing behavioral data
    subjects_missing_behavior = df[~behavioral_valid_mask]
    count_missing_behavior = len(subjects_missing_behavior)
    
    # Check for motion artifact flags if available
    # Assuming a column 'exclusion_reason' or similar might exist, or we infer from specific patterns
    # If the metadata has an explicit 'exclusion_reason' column:
    motion_mask = None
    if 'exclusion_reason' in df.columns:
        motion_mask = df['exclusion_reason'].str.lower().str.contains('motion', na=False)
        motion_count = motion_mask.sum() if motion_mask is not None else 0
    else:
        # Fallback: if we don't have explicit reasons, we assume missing behavioral data is the primary cause
        # unless the project spec defines a specific motion column.
        # For this task, we will treat missing behavioral data as the primary failure mode.
        motion_count = 0
        motion_mask = pd.Series([False] * len(df), index=df.index)

    # Calculate retention rate based on valid behavioral data
    retention_rate = count_valid_behavior / total_subjects if total_subjects > 0 else 0.0
    
    metrics = {
        "total_subjects": total_subjects,
        "retained_subjects": count_valid_behavior,
        "retention_rate": retention_rate,
        "missing_behavioral_count": count_missing_behavior,
        "missing_behavioral_reason": "missing_pre_post_scores",
        "motion_artifact_count": motion_count,
        "threshold_met": retention_rate >= min_retention_rate
    }
    
    # Decision Logic
    if retention_rate < min_retention_rate:
        # Check if the missing data is primarily due to motion artifacts (if we could distinguish)
        # The task says: "If < 80% due to missing behavioral data, log Fatal... If < 80% due to motion, log warning"
        # Since we can't perfectly distinguish without more data, we default to the stricter check:
        # If we have explicit motion flags and the majority of missing is motion, we warn.
        # Otherwise, we assume missing behavioral data is the issue.
        
        is_motion_dominant = False
        if motion_count > 0 and count_missing_behavior > 0:
            if motion_count >= count_missing_behavior:
                is_motion_dominant = True
        
        if is_motion_dominant:
            logger.warning(f"Retention rate ({retention_rate:.2%}) is below threshold ({min_retention_rate:.2%}) due to motion artifacts. Proceeding with caution.")
            # Proceed but save the warning metrics
        else:
            fatal_msg = f"Fatal: Retention < {min_retention_rate:.0%} due to missing behavioral data."
            logger.error(fatal_msg)
            # Save metrics before exiting to satisfy SC-001 logging requirement
            with open(output_path, 'w') as f:
                json.dump(metrics, f, indent=2)
            raise RuntimeError(fatal_msg)
    else:
        logger.info(f"Retention rate ({retention_rate:.2%}) meets threshold ({min_retention_rate:.2%}).")
    
    # Save metrics
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    logger.info(f"Retention metrics saved to {output_path}")
    return True, metrics

def main():
    """Entry point for T003 execution."""
    # Setup logger
    setup_logger()
    
    # Paths based on project structure
    metadata_path = "data/raw/metadata.csv"
    output_path = "data/processed/behavioral/retention_metrics.json"
    
    try:
        success, metrics = validate_retention_and_behavioral_data(metadata_path, output_path)
        if success:
            logger.info("Validation passed.")
        else:
            logger.warning("Validation completed but thresholds were not met (handled by exception in strict mode).")
    except RuntimeError as e:
        logger.critical(str(e))
        # Exit with error code to block pipeline
        import sys
        sys.exit(1)
    except Exception as e:
        logger.critical(f"Unexpected error during validation: {e}")
        import sys
        sys.exit(1)

if __name__ == "__main__":
    main()
