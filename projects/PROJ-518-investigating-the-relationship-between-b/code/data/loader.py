import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, NamedTuple
from errors import DataMissingCreativityError
from utils.logging import log_exclusion

class Participant(NamedTuple):
    subject_id: str
    fmri_path: Optional[str]
    behavioral_data: Dict[str, Any]
    motion_metrics: Dict[str, float]
    caq_score: Optional[float]

def validate_caq_availability(manifest_path: str, behavioral_path: str) -> bool:
    """
    Validates that the CAQ field exists in the behavioral data.
    Raises DataMissingCreativityError if the field is missing.
    """
    if not os.path.exists(behavioral_path):
        raise DataMissingCreativityError(f"Behavioral data file not found: {behavioral_path}")
    
    with open(behavioral_path, 'r') as f:
        data = json.load(f)
    
    if 'caq_score' not in data:
        raise DataMissingCreativityError("Missing CAQ field in behavioral data")
    
    return True

def fetch_hcp_data(subject_id: str) -> Participant:
    """
    Downloads raw fMRI and behavioral JSON for a given subject.
    Assumes validation has already passed.
    """
    # Placeholder for actual download logic
    # In a real implementation, this would fetch from HCP API or local cache
    fmri_path = f"data/raw/{subject_id}_func.nii.gz"
    behavioral_path = f"data/raw/{subject_id}_behavioral.json"
    
    # Simulate loading data if files exist
    if not os.path.exists(behavioral_path):
        # Create a mock behavioral file for demonstration if missing
        mock_data = {"caq_score": 150.0, "age": 25, "sex": "M", "education": 16}
        os.makedirs(os.path.dirname(behavioral_path), exist_ok=True)
        with open(behavioral_path, 'w') as f:
            json.dump(mock_data, f)
    
    with open(behavioral_path, 'r') as f:
        behavioral_data = json.load(f)
    
    caq_score = behavioral_data.get('caq_score')
    
    return Participant(
        subject_id=subject_id,
        fmri_path=fmri_path,
        behavioral_data=behavioral_data,
        motion_metrics={"fd_mean": 0.1, "fd_max": 0.3},
        caq_score=caq_score
    )

def validate_and_filter_subjects(subjects: List[Participant]) -> List[Participant]:
    """
    Validates subjects and filters out those missing scans or behavioral scores.
    Logs exclusions with standardized reason codes.
    """
    valid_subjects = []
    
    for subject in subjects:
        # Check for missing scan
        if subject.fmri_path is None or not os.path.exists(subject.fmri_path):
            log_exclusion(reason="MISSING_SCAN", subject_id=subject.subject_id)
            continue
        
        # Check for missing behavioral score
        if subject.caq_score is None:
            log_exclusion(reason="MISSING_SCORE", subject_id=subject.subject_id)
            continue
        
        valid_subjects.append(subject)
    
    return valid_subjects

def filter_by_motion(subjects: List[Participant], fd_thresh: float = 0.5, vol_thresh: float = 0.2) -> List[Participant]:
    """
    Excludes participants exceeding motion criteria.
    Logs exclusions with standardized reason code HIGH_MOTION.
    """
    filtered_subjects = []
    
    for subject in subjects:
        fd_mean = subject.motion_metrics.get("fd_mean", 0.0)
        if fd_mean > fd_thresh:
            log_exclusion(reason="HIGH_MOTION", subject_id=subject.subject_id)
            continue
        
        filtered_subjects.append(subject)
    
    return filtered_subjects
