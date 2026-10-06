import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, NamedTuple
from dataclasses import dataclass
import logging

from errors import DataMissingCreativityError
from utils.logging import log_exclusion
from config import get_config

@dataclass
class Participant:
    subject_id: str
    fmri_path: Optional[str]
    behavioral_data: Dict[str, Any]
    age: Optional[int] = None
    sex: Optional[str] = None
    education: Optional[int] = None
    motion_metrics: Optional[Dict[str, float]] = None

def validate_caq_availability(manifest_path: str, behavioral_path: str) -> bool:
    """
    Validates that the CAQ field exists in the behavioral data.
    Raises DataMissingCreativityError if the field is missing.
    """
    config = get_config()
    if not os.path.exists(manifest_path):
        raise FileNotFoundError(f"Manifest file not found: {manifest_path}")
    
    try:
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in manifest: {e}")

    # Check if CAQ key exists in behavioral data structure
    # Assuming manifest contains a 'behavioral' key or similar structure
    # Based on typical structure, we check for the specific field
    if 'behavioral' not in manifest:
        raise DataMissingCreativityError("MISSING_FIELD: 'behavioral' key not found in manifest")
    
    if 'CAQ' not in manifest['behavioral']:
        raise DataMissingCreativityError("MISSING_FIELD: 'CAQ' field not found in behavioral data")
    
    return True

def fetch_hcp_data(subject_id: str):
    """
    Downloads raw fMRI and behavioral JSON for a specific subject.
    This function is called AFTER validation succeeds.
    """
    config = get_config()
    # Implementation would depend on HCP API or local storage structure
    # Placeholder for actual download logic
    fmri_path = os.path.join(config.DATA_PATH, f"{subject_id}_fMRI.nii.gz")
    behavioral_path = os.path.join(config.DATA_PATH, f"{subject_id}_behavioral.json")
    
    if not os.path.exists(fmri_path) or not os.path.exists(behavioral_path):
        # In a real scenario, this would download from HCP
        raise FileNotFoundError(f"Data files not found for subject {subject_id}")
    
    return {"fmri": fmri_path, "behavioral": behavioral_path}

def validate_and_filter_subjects(subjects: List[Participant]) -> List[Participant]:
    """
    Validates and filters subjects based on scan availability and behavioral scores.
    
    Exclusion Logic:
    1. Missing scans: Log warning, skip subject.
    2. Missing behavioral scores: Exclude subject, log with reason 'MISSING_SCORE'.
    
    Args:
        subjects: List of Participant objects.
        
    Returns:
        List of filtered Participant objects.
    """
    filtered_subjects = []
    
    for subject in subjects:
        # Check for missing scans
        if subject.fmri_path is None or not os.path.exists(subject.fmri_path):
            # Log warning (using standard logging for warnings, not exclusion log)
            logging.warning(f"Subject {subject.subject_id} has missing scan. Skipping.")
            continue
        
        # Check for missing behavioral scores (CAQ)
        if subject.behavioral_data is None or 'CAQ' not in subject.behavioral_data:
            # Exclude and log with standardized reason code
            log_exclusion(reason="MISSING_SCORE", subject_id=subject.subject_id)
            continue
        
        filtered_subjects.append(subject)
        
    return filtered_subjects

def filter_by_motion(subjects: List[Participant], fd_thresh: float = 0.5, vol_thresh: float = 0.2) -> List[Participant]:
    """
    Excludes participants exceeding motion criteria.
    
    Args:
        subjects: List of Participant objects.
        fd_thresh: Threshold for mean Framewise Displacement.
        vol_thresh: Threshold for high-motion volumes percentage.
        
    Returns:
        List of filtered Participant objects.
    """
    filtered_subjects = []
    
    for subject in subjects:
        if subject.motion_metrics is None:
            # If no motion metrics available, we might exclude or warn.
            # Assuming we exclude if metrics are missing to be safe.
            log_exclusion(reason="HIGH_MOTION", subject_id=subject.subject_id)
            continue
        
        mean_fd = subject.motion_metrics.get('mean_fd', 0.0)
        high_vol_pct = subject.motion_metrics.get('high_vol_pct', 0.0)
        
        if mean_fd > fd_thresh or high_vol_pct > vol_thresh:
            # Exclude and log with standardized reason code
            log_exclusion(reason="HIGH_MOTION", subject_id=subject.subject_id)
            continue
        
        filtered_subjects.append(subject)
        
    return filtered_subjects
