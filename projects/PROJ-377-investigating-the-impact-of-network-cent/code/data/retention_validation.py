"""
Retention Validation Module for US1.

This module implements the validation logic to ensure >= 80% subject retention
and handles graceful failure if behavioral data is missing.

It reads retention metrics calculated in Phase 0/1, validates them against
the threshold, and logs the results.
"""
import os
import json
import logging
import pandas as pd
from pathlib import Path
from typing import Tuple, List, Optional
from utils.logging import setup_logger

# Constants
RETENTION_THRESHOLD = 0.80
LOG_PATH = Path("data/processed/logs")
METRICS_PATH = Path("data/processed/behavioral/retention_metrics.json")
BEHAVIORAL_DATA_PATH = Path("data/processed/behavioral/subject_scores.csv")

def setup_module_logger():
    """Configure logger for this module."""
    return setup_logger("retention_validation", LOG_PATH / "retention_validation.log")

def load_retention_metrics(logger: logging.Logger) -> Optional[dict]:
    """
    Load retention metrics from the JSON file generated in Phase 0.

    Args:
        logger: Logger instance.

    Returns:
        Dictionary containing retention metrics or None if file missing.
    """
    if not METRICS_PATH.exists():
        logger.error(f"Retention metrics file not found: {METRICS_PATH}")
        return None

    try:
        with open(METRICS_PATH, 'r') as f:
            data = json.load(f)
        logger.info(f"Loaded retention metrics: {data}")
        return data
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse retention metrics JSON: {e}")
        return None

def load_behavioral_data(logger: logging.Logger) -> Optional[pd.DataFrame]:
    """
    Load the behavioral data CSV to verify its existence and integrity.

    Args:
        logger: Logger instance.

    Returns:
        DataFrame with behavioral data or None if missing/invalid.
    """
    if not BEHAVIORAL_DATA_PATH.exists():
        logger.warning(f"Behavioral data file not found: {BEHAVIORAL_DATA_PATH}")
        return None

    try:
        df = pd.read_csv(BEHAVIORAL_DATA_PATH)
        required_cols = ['subject_id', 'pre_motor_score', 'post_motor_score', 'age', 'sex', 'improvement_score']
        missing_cols = [c for c in required_cols if c not in df.columns]
        if missing_cols:
            logger.error(f"Behavioral data missing required columns: {missing_cols}")
            return None
        
        # Check for missing values in critical columns
        if df['improvement_score'].isnull().any():
            logger.warning("Behavioral data contains missing improvement scores.")
        
        logger.info(f"Loaded behavioral data with {len(df)} subjects.")
        return df
    except Exception as e:
        logger.error(f"Failed to load behavioral data: {e}")
        return None

def validate_retention_threshold(metrics: dict, logger: logging.Logger) -> Tuple[bool, str]:
    """
    Validate that the retention rate meets the >= 80% threshold.

    Args:
        metrics: Dictionary containing 'retention_rate' and 'retention_reason'.
        logger: Logger instance.

    Returns:
        Tuple of (is_valid, message).
    """
    retention_rate = metrics.get('retention_rate')
    retention_reason = metrics.get('retention_reason', 'unknown')

    if retention_rate is None:
        msg = "Fatal: Retention rate not found in metrics."
        logger.error(msg)
        return False, msg

    if retention_rate < RETENTION_THRESHOLD:
        if retention_reason == "missing_behavioral":
            msg = f"Fatal: Retention rate ({retention_rate:.2%}) is below {RETENTION_THRESHOLD:.0%} due to missing behavioral data. Aborting."
            logger.error(msg)
            return False, msg
        elif retention_reason == "motion_artifacts":
            msg = f"Warning: Retention rate ({retention_rate:.2%}) is below {RETENTION_THRESHOLD:.0%} due to motion artifacts. Proceeding with caution."
            logger.warning(msg)
            return True, msg
        else:
            msg = f"Fatal: Retention rate ({retention_rate:.2%}) is below {RETENTION_THRESHOLD:.0%}. Aborting."
            logger.error(msg)
            return False, msg
    else:
        msg = f"Success: Retention rate ({retention_rate:.2%}) meets threshold ({RETENTION_THRESHOLD:.0%})."
        logger.info(msg)
        return True, msg

def generate_exclusion_log(logger: logging.Logger) -> None:
    """
    Generate a detailed log of excluded subjects based on the behavioral data and retention metrics.
    This fulfills the requirement to log exclusions gracefully.
    """
    LOG_PATH.mkdir(parents=True, exist_ok=True)
    exclusion_log_path = LOG_PATH / "exclusion_log.csv"
    
    # Load behavioral data to identify valid subjects
    behavioral_df = load_behavioral_data(logger)
    
    # Load raw metadata if available to cross-reference (optional, but good for completeness)
    raw_metadata_path = Path("data/raw/metadata.csv")
    raw_df = None
    if raw_metadata_path.exists():
        try:
            raw_df = pd.read_csv(raw_metadata_path)
        except Exception:
            pass

    excluded_subjects = []
    
    if behavioral_df is not None:
        # Identify subjects in behavioral data
        valid_subjects = set(behavioral_df['subject_id'].dropna().unique())
        
        if raw_df is not None:
            all_subjects = set(raw_df['subject_id'].dropna().unique())
            excluded_ids = all_subjects - valid_subjects
            
            for sid in excluded_ids:
                excluded_subjects.append({
                    'subject_id': sid,
                    'reason': 'missing_behavioral_data',
                    'details': 'Subject present in raw metadata but missing from processed behavioral scores.'
                })
        else:
            logger.warning("Raw metadata not found; cannot cross-reference exclusions.")
    
    # Add any subjects explicitly flagged as excluded in behavioral data (e.g. NaN scores)
    if behavioral_df is not None:
        nan_rows = behavioral_df[behavioral_df['improvement_score'].isnull()]
        for _, row in nan_rows.iterrows():
            excluded_subjects.append({
                'subject_id': row['subject_id'],
                'reason': 'invalid_behavioral_score',
                'details': 'Improvement score is NaN or invalid.'
            })

    # Create DataFrame and save
    if excluded_subjects:
        exclusion_df = pd.DataFrame(excluded_subjects)
        exclusion_df.to_csv(exclusion_log_path, index=False)
        logger.info(f"Saved exclusion log with {len(excluded_subjects)} entries to {exclusion_log_path}")
    else:
        # Create empty log with headers to indicate validation occurred
        exclusion_df = pd.DataFrame(columns=['subject_id', 'reason', 'details'])
        exclusion_df.to_csv(exclusion_log_path, index=False)
        logger.info(f"No exclusions found. Created empty log at {exclusion_log_path}")

def run_retention_validation() -> bool:
    """
    Main entry point for retention validation.
    
    Returns:
        True if validation passes, False if it fails (fatal error).
    """
    logger = setup_module_logger()
    logger.info("Starting Retention Validation (T019)...")

    # 1. Load Metrics
    metrics = load_retention_metrics(logger)
    if not metrics:
        logger.error("Cannot proceed without retention metrics.")
        return False

    # 2. Validate Threshold
    is_valid, message = validate_retention_threshold(metrics, logger)
    
    if not is_valid:
        # If fatal, we stop. If warning, we proceed but log.
        if "Fatal" in message:
            return False

    # 3. Load Behavioral Data to ensure it exists
    behavioral_df = load_behavioral_data(logger)
    if behavioral_df is None:
        logger.error("Behavioral data is missing or invalid. Cannot proceed.")
        return False

    # 4. Generate Exclusion Log (T020 dependency, but executed here for T019 logging requirement)
    generate_exclusion_log(logger)

    logger.info("Retention Validation completed successfully.")
    return True

def main():
    """Script entry point."""
    success = run_retention_validation()
    if not success:
        exit(1)

if __name__ == "__main__":
    main()