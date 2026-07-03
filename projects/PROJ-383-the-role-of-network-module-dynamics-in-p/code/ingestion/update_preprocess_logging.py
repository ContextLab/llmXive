"""
Update preprocess.py to integrate logging for subject exclusions.

This module modifies the existing preprocess.py to add logging calls
for subject exclusions due to missing behavioral scores or excessive motion.
It ensures that all exclusion events are properly logged with context.
"""
import sys
import os
import json
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

# Import existing functions
from ingestion.preprocess import calculate_mean_fd, check_subject_exclusion, process_subject_exclusions, scrub_and_regression, calculate_fd_series
from utils.logging_config import setup_logging
from ingestion.logging_integration import (
    log_missing_behavioral_scores,
    log_excessive_motion,
    log_subject_processing,
    get_exclusion_summary
)


def process_subject_with_logging(
    subject_id: str,
    fmri_path: Path,
    behavioral_path: Path,
    motion_path: Path,
    fd_threshold: float = 0.2
) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """
    Process a single subject with comprehensive logging.
    
    Args:
        subject_id: HCP subject identifier
        fmri_path: Path to fMRI data
        behavioral_path: Path to behavioral data
        motion_path: Path to motion parameters
        fd_threshold: FD threshold for exclusion
        
    Returns:
        Tuple of (was_included, exclusion_details or None)
    """
    exclusion_details = None
    
    # Check for missing behavioral data
    if not behavioral_path.exists():
        log_missing_behavioral_scores(
            subject_id=subject_id,
            reason="Behavioral data file not found",
            missing_fields=["accuracy_2back"],
            file_path=str(behavioral_path)
        )
        return False, {"reason": "missing_behavioral", "file": str(behavioral_path)}
    
    try:
        behavioral_df = pd.read_parquet(behavioral_path) if behavioral_path.suffix == '.parquet' else pd.read_csv(behavioral_path)
        if 'accuracy_2back' not in behavioral_df.columns:
            log_missing_behavioral_scores(
                subject_id=subject_id,
                reason="2-back accuracy column missing",
                missing_fields=["accuracy_2back"],
                file_path=str(behavioral_path)
            )
            return False, {"reason": "missing_column", "column": "accuracy_2back"}
    except Exception as e:
        log_missing_behavioral_scores(
            subject_id=subject_id,
            reason=f"Failed to read behavioral data: {str(e)}",
            file_path=str(behavioral_path)
        )
        return False, {"reason": "read_error", "error": str(e)}
    
    # Calculate mean FD
    try:
        fd_series = calculate_fd_series(motion_path)
        mean_fd = calculate_mean_fd(fd_series)
    except Exception as e:
        log_excessive_motion(
            subject_id=subject_id,
            mean_fd=0.0,
            threshold=fd_threshold,
            fd_series_path=str(motion_path)
        )
        return False, {"reason": "fd_calculation_error", "error": str(e)}
    
    # Check for excessive motion
    if mean_fd > fd_threshold:
        log_excessive_motion(
            subject_id=subject_id,
            mean_fd=mean_fd,
            threshold=fd_threshold,
            fd_series_path=str(motion_path)
        )
        return False, {"reason": "excessive_motion", "mean_fd": mean_fd}
    
    # Subject passes all checks
    log_subject_processing(
        subject_id=subject_id,
        status="included",
        details={
            "mean_fd": mean_fd,
            "behavioral_score": behavioral_df['accuracy_2back'].mean() if 'accuracy_2back' in behavioral_df.columns else None
        }
    )
    
    return True, {"mean_fd": mean_fd}


def run_logging_aware_ingestion(
    subjects: List[str],
    base_dir: Path,
    output_dir: Path,
    fd_threshold: float = 0.2
) -> Dict[str, Any]:
    """
    Run ingestion with comprehensive logging for all subjects.
    
    Args:
        subjects: List of subject IDs to process
        base_dir: Base directory containing raw data
        output_dir: Directory for processed data
        fd_threshold: FD threshold for exclusion
        
    Returns:
        Summary dictionary with processing results
    """
    excluded_subjects = []
    included_subjects = []
    
    for subject_id in subjects:
        fmri_path = base_dir / f"sub-{subject_id}" / "func" / "rest.nii.gz"
        behavioral_path = base_dir / f"sub-{subject_id}" / "behavior" / "nback.parquet"
        motion_path = base_dir / f"sub-{subject_id}" / "func" / "realign.par"
        
        was_included, details = process_subject_with_logging(
            subject_id=subject_id,
            fmri_path=fmri_path,
            behavioral_path=behavioral_path,
            motion_path=motion_path,
            fd_threshold=fd_threshold
        )
        
        if was_included:
            included_subjects.append(subject_id)
        else:
            excluded_subjects.append({
                "subject_id": subject_id,
                "details": details
            })
    
    summary = get_exclusion_summary(excluded_subjects, included_subjects)
    
    # Save summary to file
    summary_path = output_dir / "exclusion_summary.json"
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    logging.info(f"Exclusion summary saved to {summary_path}")
    return summary


def main() -> None:
    """
    Main function to run logging-aware ingestion.
    
    This function sets up logging and processes a sample of subjects
    to demonstrate the logging integration.
    """
    # Setup logging
    log_file = Path("data/logs/ingestion_with_logging.log")
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    setup_logging(
        log_file=log_file,
        level=logging.INFO
    )
    
    logging.info("Starting logging-aware ingestion pipeline")
    
    # Sample subjects for demonstration
    sample_subjects = ["100307", "100408", "100509", "100610", "100711"]
    
    # In a real scenario, these paths would point to actual data
    base_dir = Path("data/raw_fmri")
    output_dir = Path("data/results")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Run ingestion with logging
    summary = run_logging_aware_ingestion(
        subjects=sample_subjects,
        base_dir=base_dir,
        output_dir=output_dir,
        fd_threshold=0.2
    )
    
    logging.info(f"Ingestion completed. Summary: {summary}")


if __name__ == "__main__":
    main()
