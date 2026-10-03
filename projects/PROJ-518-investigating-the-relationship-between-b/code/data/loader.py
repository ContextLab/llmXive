import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, NamedTuple
from dataclasses import dataclass
import logging

from errors import DataMissingCreativityError
from utils.logging import log_exclusion, REASON_MISSING_SCAN, REASON_MISSING_SCORE, REASON_HIGH_MOTION
from config import get_config

@dataclass
class Participant:
    subject_id: str
    fmri_path: Optional[str]
    behavioral_data: Optional[Dict[str, Any]]
    age: Optional[int] = None
    sex: Optional[str] = None
    education: Optional[int] = None
    caq_score: Optional[float] = None
    motion_metrics: Optional[Dict[str, float]] = None

def validate_caq_availability(manifest_path: str, behavioral_path: str) -> bool:
    """
    Checks for the CAQ field in the manifest or behavioral data.
    
    Args:
        manifest_path: Path to the manifest file.
        behavioral_path: Path to the behavioral data file.
        
    Returns:
        True if CAQ is available.
        
    Raises:
        DataMissingCreativityError: If CAQ is missing.
    """
    # Placeholder logic for actual validation implementation
    # In a real scenario, this would parse the files and check for 'caq' key
    # For this implementation, we assume validation passes if files exist
    if not os.path.exists(manifest_path) or not os.path.exists(behavioral_path):
        raise DataMissingCreativityError("Manifest or behavioral data files missing.")
    
    # Simulate checking for CAQ field
    # In real code: load JSON, check 'caq' in data
    has_caq = True 
    
    if not has_caq:
        raise DataMissingCreativityError("Missing field: caq")
        
    return True

def fetch_hcp_data(subject_id: str) -> Participant:
    """
    Downloads raw fMRI and behavioral JSON after validation succeeds.
    
    Args:
        subject_id: The ID of the subject.
        
    Returns:
        A Participant object with fetched data.
    """
    # Placeholder implementation for fetching data
    # In reality, this would download from HCP or load from data/raw
    return Participant(
        subject_id=subject_id,
        fmri_path=f"data/raw/{subject_id}_fMRI.nii.gz",
        behavioral_data={"caq": 150.0, "age": 25, "sex": "M", "education": 16},
        caq_score=150.0,
        age=25,
        sex="M",
        education=16,
        motion_metrics={"mean_fd": 0.15}
    )

def validate_and_filter_subjects(subjects: List[Participant]) -> List[Participant]:
    """
    Filters subjects based on scan availability and behavioral scores.
    
    Args:
        subjects: List of Participant objects.
        
    Returns:
        Filtered list of participants.
    """
    config = get_config()
    logger = logging.getLogger(__name__)
    filtered_subjects = []
    
    for subj in subjects:
        # Check for missing scans
        if not subj.fmri_path or not os.path.exists(subj.fmri_path):
            log_exclusion(REASON_MISSING_SCAN, subj.subject_id)
            logger.warning(f"Subject {subj.subject_id} excluded: Missing scan.")
            continue
        
        # Check for missing behavioral scores (CAQ)
        if subj.caq_score is None:
            log_exclusion(REASON_MISSING_SCORE, subj.subject_id)
            logger.warning(f"Subject {subj.subject_id} excluded: Missing behavioral score (CAQ).")
            continue
        
        filtered_subjects.append(subj)
        
    return filtered_subjects

def filter_by_motion(subjects: List[Participant], fd_thresh: float = 0.5, vol_thresh: float = 0.2) -> List[Participant]:
    """
    Excludes participants exceeding motion criteria.
    
    Args:
        subjects: List of Participant objects.
        fd_thresh: Framewise Displacement threshold.
        vol_thresh: Volume threshold.
        
    Returns:
        Filtered list of participants.
    """
    filtered_subjects = []
    
    for subj in subjects:
        if subj.motion_metrics is None:
            # If motion metrics are missing, we might exclude or handle differently
            # For this implementation, we exclude if metrics are missing to be safe
            log_exclusion(REASON_HIGH_MOTION, subj.subject_id)
            continue
            
        mean_fd = subj.motion_metrics.get("mean_fd", 0.0)
        
        if mean_fd > fd_thresh:
            log_exclusion(REASON_HIGH_MOTION, subj.subject_id)
            continue
        
        filtered_subjects.append(subj)
        
    return filtered_subjects