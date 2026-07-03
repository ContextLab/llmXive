"""
Logging integration for subject exclusions in the HCP data ingestion pipeline.

This module provides the infrastructure to log subject exclusions due to:
1. Missing behavioral scores (2-back accuracy)
2. Excessive motion (mean FD > 0.2mm)

It integrates with the existing logging configuration and ensures all
exclusion events are recorded with appropriate context for reproducibility.
"""
import logging
import os
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

# Import existing logging configuration
from utils.logging_config import setup_logging, log_subject_exclusion, log_memory_usage


def log_missing_behavioral_scores(
    subject_id: str,
    reason: str,
    missing_fields: Optional[List[str]] = None,
    file_path: Optional[str] = None
) -> None:
    """
    Log a subject exclusion due to missing behavioral scores.
    
    Args:
        subject_id: The HCP subject identifier (e.g., '100307')
        reason: Detailed reason for exclusion
        missing_fields: List of specific missing behavioral fields
        file_path: Path to the subject's behavioral data file if available
    """
    context = {
        "exclusion_type": "missing_behavioral_scores",
        "subject_id": subject_id,
        "missing_fields": missing_fields or [],
        "file_path": file_path,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    log_subject_exclusion(
        subject_id=subject_id,
        reason=reason,
        context=context
    )
    
    logging.warning(
        f"Subject {subject_id} excluded: missing behavioral scores. "
        f"Reason: {reason}"
    )


def log_excessive_motion(
    subject_id: str,
    mean_fd: float,
    threshold: float = 0.2,
    fd_series_path: Optional[str] = None
) -> None:
    """
    Log a subject exclusion due to excessive motion.
    
    Args:
        subject_id: The HCP subject identifier
        mean_fd: Calculated mean framewise displacement
        threshold: FD threshold used for exclusion (default 0.2mm)
        fd_series_path: Path to the FD time series file if available
    """
    context = {
        "exclusion_type": "excessive_motion",
        "subject_id": subject_id,
        "mean_fd": mean_fd,
        "threshold": threshold,
        "fd_series_path": fd_series_path,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    log_subject_exclusion(
        subject_id=subject_id,
        reason=f"Mean FD {mean_fd:.4f}mm exceeds threshold {threshold}mm",
        context=context
    )
    
    logging.warning(
        f"Subject {subject_id} excluded: excessive motion. "
        f"Mean FD: {mean_fd:.4f}mm (threshold: {threshold}mm)"
    )


def log_subject_processing(
    subject_id: str,
    status: str,
    details: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log the processing status of a subject.
    
    Args:
        subject_id: The HCP subject identifier
        status: Processing status ('included', 'excluded', 'error')
        details: Additional processing details
    """
    context = {
        "subject_id": subject_id,
        "status": status,
        "details": details or {},
        "timestamp": datetime.utcnow().isoformat()
    }
    
    log_msg = f"Subject {subject_id} processing: {status}"
    if details:
        log_msg += f" - {details}"
    
    if status == "included":
        logging.info(log_msg)
    elif status == "excluded":
        logging.warning(log_msg)
    else:
        logging.error(log_msg)


def get_exclusion_summary(
    excluded_subjects: List[Dict[str, Any]],
    included_subjects: List[str]
) -> Dict[str, Any]:
    """
    Generate a summary of subject exclusions and inclusions.
    
    Args:
        excluded_subjects: List of exclusion records
        included_subjects: List of included subject IDs
        
    Returns:
        Summary dictionary with counts and breakdown by exclusion reason
    """
    exclusion_reasons = {}
    for record in excluded_subjects:
        reason = record.get("reason", "unknown")
        exclusion_reasons[reason] = exclusion_reasons.get(reason, 0) + 1
    
    return {
        "total_subjects_processed": len(excluded_subjects) + len(included_subjects),
        "subjects_included": len(included_subjects),
        "subjects_excluded": len(excluded_subjects),
        "exclusion_breakdown": exclusion_reasons,
        "inclusion_rate": len(included_subjects) / (len(excluded_subjects) + len(included_subjects)) if (len(excluded_subjects) + len(included_subjects)) > 0 else 0.0
    }


def main() -> None:
    """
    Main function to demonstrate logging integration.
    
    This function sets up logging and logs sample exclusion events
    to verify the logging infrastructure is working correctly.
    """
    # Setup logging
    log_file = Path("data/logs/ingestion.log")
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    setup_logging(
        log_file=log_file,
        level=logging.INFO
    )
    
    logging.info("Starting logging integration test")
    
    # Log sample exclusions
    log_missing_behavioral_scores(
        subject_id="100307",
        reason="2-back accuracy file not found",
        missing_fields=["accuracy_2back"]
    )
    
    log_excessive_motion(
        subject_id="100408",
        mean_fd=0.25,
        threshold=0.2
    )
    
    log_subject_processing(
        subject_id="100509",
        status="included",
        details={"mean_fd": 0.15, "behavioral_score": 0.82}
    )
    
    # Generate summary
    excluded = [
        {"subject_id": "100307", "reason": "missing_behavioral_scores"},
        {"subject_id": "100408", "reason": "excessive_motion"}
    ]
    included = ["100509", "100610", "100711"]
    
    summary = get_exclusion_summary(excluded, included)
    logging.info(f"Exclusion summary: {summary}")
    
    logging.info("Logging integration test completed")


if __name__ == "__main__":
    main()
