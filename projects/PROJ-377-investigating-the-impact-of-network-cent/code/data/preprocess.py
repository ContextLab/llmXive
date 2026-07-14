import os
import json
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
import time

# Local imports matching the provided API surface
from utils.config import get_config, get_dataset_config, get_preprocessing_config, get_min_retention_rate, get_fd_threshold
from utils.logging import setup_logger, log_memory_usage, Timer
from data.subject import Subject
from data.connectivity_matrix import ConnectivityMatrix

# Configure logger for this module
logger = setup_logger(__name__)

def _log_excluded_subject(subject_id: str, reason: str, details: Optional[Dict[str, Any]] = None):
    """
    Logs the exclusion of a subject with the specific reason and optional details.
    This function ensures a structured audit trail for data exclusion.
    """
    log_msg = f"Subject {subject_id} EXCLUDED: {reason}"
    if details:
        log_msg += f" | Details: {json.dumps(details)}"
    logger.warning(log_msg)

def _check_behavioral_data(subject: Subject, config) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    Validates that a subject has the required behavioral data (pre/post scores).
    Returns (is_valid, reason, details).
    """
    if not subject.has_behavioral_data():
        return False, "Missing behavioral data (pre/post scores)", None
    
    pre_score = subject.get_pre_score()
    post_score = subject.get_post_score()
    
    if pd.isna(pre_score) or pd.isna(post_score):
        return False, "Missing numerical behavioral scores (NaN)", {"pre": pre_score, "post": post_score}
    
    # Optional: Check for impossible scores if domain knowledge exists
    # For now, we assume valid range is handled by data ingestion
    return True, "", None

def _check_motion_outlier(subject: Subject, config) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    Checks if a subject's mean Framewise Displacement (FD) exceeds the threshold.
    Returns (is_valid, reason, details).
    """
    mean_fd = subject.get_mean_fd()
    if mean_fd is None:
        # If FD couldn't be calculated, we might exclude or warn depending on config
        # Strict mode: exclude if FD is missing
        return False, "Missing Mean FD calculation", None
    
    threshold = get_fd_threshold()
    if mean_fd > threshold:
        return False, f"Motion outlier: Mean FD ({mean_fd:.3f}) > threshold ({threshold:.3f})", {"mean_fd": mean_fd, "threshold": threshold}
    
    return True, "", None

def extract_behavioral_metrics(data_dir: Path, output_path: Path):
    """
    Extracts behavioral metrics (pre/post scores, age, sex) and calculates improvement.
    Applies exclusion logic and logs excluded subjects with reasons.
    
    Args:
        data_dir: Path to the raw/processed data directory containing subject folders.
        output_path: Path where the final behavioral CSV will be saved.
    """
    logger.info(f"Starting behavioral metric extraction from {data_dir}")
    start_time = time.time()
    
    processed_config = get_preprocessing_config()
    subjects_data = []
    excluded_subjects = []
    
    # Iterate over subject directories
    subject_dirs = [d for d in data_dir.iterdir() if d.is_dir() and d.name.startswith('sub-')]
    
    if not subject_dirs:
        logger.warning(f"No subject directories found in {data_dir}")
        # Create empty output file with headers
        output_path.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(columns=['subject_id', 'age', 'sex', 'pre_score', 'post_score', 'improvement_score', 'mean_fd', 'retention_status']).to_csv(output_path, index=False)
        return

    for s_dir in subject_dirs:
        subject_id = s_dir.name
        try:
            # Load subject data (simulated loading from T015 logic)
            # In a real scenario, this reads from the specific subject's JSON/TSV
            subject = Subject.from_directory(s_dir)
            
            if not subject:
                _log_excluded_subject(subject_id, "Failed to parse subject directory structure")
                excluded_subjects.append(subject_id)
                continue

            # Validation 1: Check behavioral data presence
            is_valid, reason, details = _check_behavioral_data(subject, processed_config)
            if not is_valid:
                _log_excluded_subject(subject_id, reason, details)
                excluded_subjects.append(subject_id)
                continue

            # Validation 2: Check motion outliers (FD)
            is_valid, reason, details = _check_motion_outlier(subject, processed_config)
            if not is_valid:
                _log_excluded_subject(subject_id, reason, details)
                excluded_subjects.append(subject_id)
                continue

            # If passed all checks
            record = {
                'subject_id': subject_id,
                'age': subject.get_age(),
                'sex': subject.get_sex(),
                'pre_score': subject.get_pre_score(),
                'post_score': subject.get_post_score(),
                'improvement_score': subject.get_post_score() - subject.get_pre_score(),
                'mean_fd': subject.get_mean_fd(),
                'retention_status': 'included'
            }
            subjects_data.append(record)

        except Exception as e:
            _log_excluded_subject(subject_id, f"Unexpected error processing subject: {str(e)}", {"error_type": type(e).__name__})
            excluded_subjects.append(subject_id)
            continue

    # Calculate retention rate
    total_subjects = len(subject_dirs)
    included_count = len(subjects_data)
    retention_rate = included_count / total_subjects if total_subjects > 0 else 0.0
    min_retention = get_min_retention_rate()
    
    logger.info(f"Extraction complete. Included: {included_count}/{total_subjects} ({retention_rate:.1%})")
    if excluded_subjects:
        logger.warning(f"Excluded {len(excluded_subjects)} subjects: {', '.join(excluded_subjects)}")
    
    if retention_rate < min_retention:
        logger.error(f"Retention rate ({retention_rate:.1%}) is below minimum threshold ({min_retention:.1%}). Process may fail or require intervention.")
    
    # Save results
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(subjects_data)
    
    if not df.empty:
        # Ensure numeric columns are correct
        numeric_cols = ['age', 'pre_score', 'post_score', 'improvement_score', 'mean_fd']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        df.to_csv(output_path, index=False)
        logger.info(f"Behavioral metrics saved to {output_path}")
    else:
        # Create empty file with schema if no data
        pd.DataFrame(columns=['subject_id', 'age', 'sex', 'pre_score', 'post_score', 'improvement_score', 'mean_fd', 'retention_status']).to_csv(output_path, index=False)
        logger.warning(f"No valid subjects found. Empty CSV saved to {output_path}")

def calculate_fd(confounds_path: Path) -> Optional[float]:
    """
    Calculates the mean Framewise Displacement from a confounds timeseries file.
    
    Args:
        confounds_path: Path to the desc-confounds_timeseries.tsv file.
        
    Returns:
        Mean FD as a float, or None if calculation fails.
    """
    try:
        # Check if file exists
        if not confounds_path.exists():
            logger.warning(f"Confounds file not found: {confounds_path}")
            return None

        # Load confounds
        # fMRIPrep confounds usually have 'trans_x', 'trans_y', 'trans_z', 'rot_x', 'rot_y', 'rot_z'
        # and a calculated 'framewise_displacement' column.
        df = pd.read_csv(confounds_path, sep='\t')
        
        if 'framewise_displacement' in df.columns:
            fd_series = df['framewise_displacement']
        else:
            # Fallback: calculate FD if column missing
            # Standard FD calculation involves differences in translation and rotation
            # This is a simplified check; real implementation might use nilearn
            logger.warning("framewise_displacement column not found. Attempting fallback calculation or returning None.")
            return None

        # Handle NaNs
        valid_fd = fd_series.dropna()
        if valid_fd.empty:
            return None
        
        return valid_fd.mean()
        
    except Exception as e:
        logger.error(f"Error calculating FD for {confounds_path}: {e}")
        return None

def preprocess_fmriprep(subject_dir: Path, output_dir: Path):
    """
    Wrapper for fMRIPrep preprocessing or loading of pre-processed data.
    In this pipeline, it primarily handles the aggregation of FD and prepares data for centrality.
    
    Args:
        subject_dir: Path to the subject's raw or preprocessed directory.
        output_dir: Path where processed outputs (like FD metrics) should be stored.
    """
    logger.info(f"Processing subject directory: {subject_dir}")
    
    # In a real pipeline, this would trigger fMRIPrep if raw data exists.
    # Here we assume fMRIPrep has run (T012) and we are extracting metrics.
    
    # Locate confounds file
    confounds_file = subject_dir / "desc-confounds_timeseries.tsv"
    if not confounds_file.exists():
        # Try standard fmriprep output structure
        potential_paths = [
            subject_dir / "func" / "desc-confounds_timeseries.tsv",
            subject_dir / "fmriprep" / "desc-confounds_timeseries.tsv"
        ]
        for p in potential_paths:
            if p.exists():
                confounds_file = p
                break
    
    if confounds_file.exists():
        mean_fd = calculate_fd(confounds_file)
        if mean_fd is not None:
            logger.info(f"Subject {subject_dir.name} Mean FD: {mean_fd:.4f}")
            # Store FD in a temporary location for Subject object or direct usage
            # In a full implementation, we might write this to a central metrics CSV here
        else:
            logger.warning(f"Could not calculate Mean FD for {subject_dir.name}")
    else:
        logger.warning(f"No confounds file found for {subject_dir.name}")

    # Placeholder for actual fMRIPrep execution if needed
    # subprocess.run(...) would go here if we were running the tool