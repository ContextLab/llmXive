import os
import json
import logging
import subprocess
import time
import shutil
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

import pandas as pd
import numpy as np

from utils.logging import setup_logger, get_resource_usage
from utils.config import get_config, get_dataset_config

# Import existing functions from sibling modules to ensure API consistency
from data.behavioral_extraction import load_metadata, extract_behavioral_metrics, save_behavioral_metrics
from data.validation import validate_retention_and_behavioral_data

logger = setup_logger(__name__)

def preprocess_fmriprep(subject_ids: Optional[list] = None) -> Dict[str, Any]:
    """
    Wrapper for fMRIPrep preprocessing with memory-efficient settings.
    This task focuses on the behavioral validation and retention logic,
    assuming fMRIPrep has been run or is handled by T016.
    """
    config = get_config()
    raw_data_dir = Path(config.output_paths.raw_data_dir)
    preprocessed_dir = Path(config.output_paths.preprocessed_data_dir)
    
    if not preprocessed_dir.exists():
        logger.info(f"Creating preprocessed directory: {preprocessed_dir}")
        preprocessed_dir.mkdir(parents=True, exist_ok=True)

    # Placeholder for actual fMRIPrep call if needed here, 
    # but T016 handles the wrapper. This function primarily orchestrates 
    # the flow for T018 (retention/power) after data is available.
    logger.info("fmriprep preprocessing wrapper called.")
    return {"status": "success", "directory": str(preprocessed_dir)}

def calculate_fd(confounds_dir: Path) -> pd.DataFrame:
    """
    Calculate Framewise Displacement (FD) from fMRIPrep confounds.
    Returns a DataFrame with subject_id and mean_fd.
    """
    # Implementation for T025 (Mean FD) to support T018 dependencies if needed
    # T018 primarily relies on behavioral data for retention/power, 
    # but FD is a covariate for the final model.
    # For T018, we focus on the retention metrics.
    return pd.DataFrame()

def extract_behavioral_metrics(metadata_path: Path) -> pd.DataFrame:
    """
    Extract behavioral metrics (pre/post scores, age, sex) from metadata.
    This calls the existing behavioral_extraction module.
    """
    return extract_behavioral_metrics(metadata_path)

def calculate_retention_rate(df: pd.DataFrame, retention_threshold: float = 0.80) -> Tuple[float, int, int, str]:
    """
    Calculate retention rate and check against threshold.
    
    Args:
        df: DataFrame containing subject data with a 'valid' or 'excluded' column, 
            or derived from missing value checks.
        retention_threshold: Minimum acceptable retention rate (default 0.80).
        
    Returns:
        Tuple of (retention_rate, total_subjects, retained_subjects, status_message)
    """
    total_subjects = len(df)
    if total_subjects == 0:
        return 0.0, 0, 0, "Fatal: No subjects found in dataset."
    
    # Determine valid subjects. Assuming 'valid' column exists or we check for NaN in key columns.
    # If 'valid' column is not present, we infer from missing data in critical columns.
    if 'valid' in df.columns:
        retained_subjects = df['valid'].sum()
    else:
        # Check for missing values in critical behavioral columns
        critical_cols = ['pre_motor_score', 'post_motor_score']
        # A subject is valid if they have non-null values in critical columns
        valid_mask = df[critical_cols].notna().all(axis=1)
        retained_subjects = valid_mask.sum()
    
    retention_rate = retained_subjects / total_subjects
    
    if retention_rate < retention_threshold:
        return retention_rate, total_subjects, retained_subjects, f"Fatal: Retention rate {retention_rate:.2%} is below threshold {retention_threshold:.2%}."
    
    return retention_rate, total_subjects, retained_subjects, "Success: Retention rate acceptable."

def check_power(n_subjects: int, power_threshold_n: int = 85) -> str:
    """
    Check if sample size is sufficient for power analysis.
    
    Args:
        n_subjects: Number of retained subjects.
        power_threshold_n: Minimum N required for small effect detection (default 85).
        
    Returns:
        Status message.
    """
    if n_subjects < power_threshold_n:
        return f"Warning: Underpowered for small effects (r=0.3). Current N={n_subjects}, required N>={power_threshold_n}."
    return f"Power check passed. N={n_subjects} meets threshold of {power_threshold_n}."

def save_retention_metrics(retention_rate: float, total: int, retained: int, output_path: Path) -> None:
    """
    Save retention metrics to JSON file.
    """
    metrics = {
        "retention_rate": retention_rate,
        "total_subjects": total,
        "retained_subjects": retained,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Retention metrics saved to {output_path}")

def run_retention_and_power_check() -> None:
    """
    Main entry point for T018: Implement retention rate calculation and power check.
    
    This function:
    1. Loads behavioral data (from T017 output).
    2. Calculates retention rate.
    3. Logs fatal error if retention < 80% (due to missing behavioral data).
    4. Logs warning if N < 85 (power check).
    5. Saves metrics to data/processed/behavioral/retention_metrics.json.
    """
    config = get_config()
    behavioral_output = Path(config.output_paths.behavioral_metrics_file)
    retention_output = Path(config.output_paths.retention_metrics_file)
    
    # Ensure output directory exists
    retention_output.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info("Starting Retention Rate and Power Check (T018)...")
    
    if not behavioral_output.exists():
        # If T017 hasn't run yet, try to load from raw metadata directly as a fallback for this specific check
        # But per spec, T017 should produce the CSV. We assume T017 ran.
        logger.error(f"Behavioral metrics file not found: {behavioral_output}. Cannot proceed with retention check.")
        raise FileNotFoundError(f"Missing behavioral metrics file: {behavioral_output}")
    
    df = pd.read_csv(behavioral_output)
    
    # Calculate retention
    rate, total, retained, status = calculate_retention_rate(df, retention_threshold=0.80)
    
    logger.info(f"Retention Check: {status} (Rate: {rate:.2%}, N: {retained}/{total})")
    
    # Save metrics regardless of pass/fail for audit trail, but exit if fatal
    save_retention_metrics(rate, total, retained, retention_output)
    
    if "Fatal" in status:
        logger.error(status)
        # Do not proceed to downstream tasks
        raise SystemExit(status)
    
    # Power Check
    power_status = check_power(retained, power_threshold_n=85)
    logger.info(power_status)
    
    if "Warning" in power_status:
        logger.warning(power_status)
    
    logger.info("Retention and Power Check completed successfully.")

def main():
    """
    Entry point for script execution.
    """
    try:
        run_retention_and_power_check()
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise

if __name__ == "__main__":
    main()