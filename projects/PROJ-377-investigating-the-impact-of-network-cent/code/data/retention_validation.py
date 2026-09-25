import os
import json
import logging
import pandas as pd
from pathlib import Path
from typing import Tuple, List, Optional

from utils.logging import setup_logger

logger = setup_logger(__name__)

# Constants based on tasks.md
RETENTION_THRESHOLD = 0.80
INPUT_METADATA_PATH = "data/raw/metadata.csv"
OUTPUT_RETENTION_METRICS_PATH = "data/processed/behavioral/retention_metrics.json"
REQUIRED_COLUMNS = ["pre_motor_score", "post_motor_score", "age", "sex", "subject_id"]

def load_retention_metrics() -> Optional[dict]:
    """
    Loads existing retention metrics if they exist.
    """
    path = Path(OUTPUT_RETENTION_METRICS_PATH)
    if path.exists():
        with open(path, 'r') as f:
            return json.load(f)
    return None

def load_behavioral_data() -> pd.DataFrame:
    """
    Reads the downloaded metadata from data/raw/metadata.csv.
    Validates that required columns exist (T002 check assumed passed, but re-verify here for safety).
    """
    path = Path(INPUT_METADATA_PATH)
    if not path.exists():
        raise FileNotFoundError(f"Input metadata file not found: {INPUT_METADATA_PATH}")

    df = pd.read_csv(path)

    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in metadata: {missing_cols}. "
                         "Task T002 should have caught this.")
    
    return df

def validate_retention_threshold(df: pd.DataFrame) -> Tuple[float, int, int, List[str]]:
    """
    Calculates retention rate (subjects with valid data / total subjects).
    Returns: (retention_rate, total_subjects, retained_subjects, exclusion_reasons_list)
    
    Logic:
    - A subject is 'retained' if they have valid (non-null) values for pre_motor_score AND post_motor_score.
    - We also check for motion artifacts if a 'fd_mean' or similar column exists, 
      but the task description specifically mentions 'missing behavioral data' vs 'motion artifacts'.
      Since the input is 'metadata.csv', we primarily look for missing behavioral scores.
    """
    total_subjects = len(df)
    if total_subjects == 0:
        return 0.0, 0, 0, []

    # Identify subjects with valid behavioral data
    # Valid means pre_motor_score and post_motor_score are not null/NaN
    valid_behavioral = df[REQUIRED_COLUMNS].notna().all(axis=1)
    retained_subjects = valid_behavioral.sum()
    excluded_count = total_subjects - retained_subjects

    # Determine reason for exclusion if count > 0
    # We check if the missing data is specifically the behavioral columns
    exclusion_reasons = []
    if excluded_count > 0:
        # Check for missing behavioral data specifically
        missing_behavioral = df[REQUIRED_COLUMNS].isna().any(axis=1)
        behavioral_excluded_count = missing_behavioral.sum()
        
        if behavioral_excluded_count > 0:
            exclusion_reasons.append(f"Missing behavioral data: {behavioral_excluded_count} subjects")
        
        # Check for motion artifacts if 'fd_mean' exists in metadata (optional check)
        if 'fd_mean' in df.columns:
            motion_excluded = df[~missing_behavioral][df['fd_mean'] > 0.5] # Example threshold
            if len(motion_excluded) > 0:
                exclusion_reasons.append(f"Motion artifacts (FD > 0.5): {len(motion_excluded)} subjects")

    retention_rate = retained_subjects / total_subjects if total_subjects > 0 else 0.0

    return retention_rate, total_subjects, retained_subjects, exclusion_reasons

def save_retention_metrics(rate: float, total: int, retained: int, reasons: List[str]) -> None:
    """
    Saves the retention rate proportion, total subjects, and retained subjects count
    to data/processed/behavioral/retention_metrics.json.
    """
    output_path = Path(OUTPUT_RETENTION_METRICS_PATH)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    metrics = {
        "retention_rate": rate,
        "total_subjects": total,
        "retained_subjects": retained,
        "exclusion_reasons": reasons,
        "threshold": RETENTION_THRESHOLD
    }

    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    logger.info(f"Retention metrics saved to {output_path}")

def run_retention_validation() -> None:
    """
    Main entry point for T003.
    1. Loads metadata.
    2. Calculates retention.
    3. Checks threshold.
    4. Exits if < 80% due to missing behavioral data.
    5. Warns if < 80% due to motion artifacts.
    6. Saves metrics.
    """
    logger.info("Starting Retention & Behavioral Validation (T003)...")
    
    try:
        df = load_behavioral_data()
    except FileNotFoundError as e:
        logger.error(str(e))
        raise SystemExit(1)
    except ValueError as e:
        logger.error(str(e))
        raise SystemExit(1)

    rate, total, retained, reasons = validate_retention_threshold(df)
    
    logger.info(f"Retention Analysis: {retained}/{total} subjects retained ({rate:.2%})")
    if reasons:
        for reason in reasons:
            logger.info(f"Exclusion Reason: {reason}")

    # Check thresholds
    if rate < RETENTION_THRESHOLD:
        # Determine if due to missing behavioral data
        missing_behavioral_count = df[REQUIRED_COLUMNS].isna().any(axis=1).sum()
        
        if missing_behavioral_count > 0:
            msg = "Fatal: Retention < 80% due to missing behavioral data"
            logger.error(msg)
            # Save metrics before exiting to satisfy artifact requirement
            save_retention_metrics(rate, total, retained, reasons)
            raise SystemExit(1)
        else:
            # Check if due to motion (if data available) or other reasons
            # The task says: "If < 80% due to motion artifacts, log warning and proceed."
            # If it's < 80% but NOT behavioral, we assume it might be motion or other technical issues.
            # We warn and proceed.
            msg = f"Warning: Retention < 80% ({rate:.2%}). Proceeding (assuming motion/technical artifacts)."
            logger.warning(msg)
            save_retention_metrics(rate, total, retained, reasons)
            # Proceed to next step (do not exit)
    else:
        logger.info(f"Retention rate ({rate:.2%}) meets threshold ({RETENTION_THRESHOLD:.0%}).")
        save_retention_metrics(rate, total, retained, reasons)

def main():
    run_retention_validation()

if __name__ == "__main__":
    main()
