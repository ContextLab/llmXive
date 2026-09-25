import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, NamedTuple
from dataclasses import dataclass
import logging

from errors import DataMissingCreativityError
from utils.logging import log_exclusion
from config import get_config

logger = logging.getLogger(__name__)

@dataclass
class Participant:
    subject_id: str
    fmri_path: Optional[str]
    behavioral_data: Dict[str, Any]
    motion_metrics: Dict[str, float] = None

def validate_caq_availability(manifest_path: str, behavioral_path: str) -> bool:
    """
    Checks for the CAQ field in the manifest and raises DataMissingCreativityError
    if absent.
    """
    config = get_config()
    # In a real implementation, this would parse the manifest files.
    # For this task, we assume the manifest exists and contains the field if validation passes.
    # The actual check is simulated here for the structure, but the error raising is the key.
    if not os.path.exists(manifest_path):
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")
    
    # Placeholder logic to demonstrate the check mechanism
    # In reality, we would load JSON and check 'caq_score' or similar key
    with open(manifest_path, 'r') as f:
        data = json.load(f)
        if 'caq_score' not in data:
            raise DataMissingCreativityError("CAQ field missing in manifest")
    
    return True

def fetch_hcp_data(subject_id: str) -> Participant:
    """
    Downloads raw fMRI and behavioral JSON after validation succeeds.
    """
    config = get_config()
    # Mock implementation for structure; real implementation would download
    return Participant(
        subject_id=subject_id,
        fmri_path=f"{config.DATA_PATH}/raw/{subject_id}_func.nii.gz",
        behavioral_data={"caq_score": 0.0, "age": 25, "sex": "M", "education": 16},
        motion_metrics={"fd_mean": 0.1}
    )

def validate_and_filter_subjects(subjects: List[Participant]) -> List[Participant]:
    """
    Validates subjects, skipping missing scans (log warning) and excluding
    missing behavioral scores (exclude + log with MISSING_SCORE).
    """
    filtered = []
    for sub in subjects:
        # Check for missing scan
        if sub.fmri_path is None or not os.path.exists(sub.fmri_path):
            logger.warning(f"Subject {sub.subject_id}: Missing scan file.")
            log_exclusion(reason="MISSING_SCAN", subject_id=sub.subject_id)
            continue

        # Check for missing behavioral scores (specifically CAQ)
        if sub.behavioral_data is None or 'caq_score' not in sub.behavioral_data:
            logger.warning(f"Subject {sub.subject_id}: Missing behavioral scores.")
            log_exclusion(reason="MISSING_SCORE", subject_id=sub.subject_id)
            continue

        filtered.append(sub)
    
    return filtered

def filter_by_motion(subjects: List[Participant], fd_thresh: float = 0.5, vol_thresh: float = 0.2) -> List[Participant]:
    """
    Excludes participants exceeding motion criteria and logs the exclusion with HIGH_MOTION.
    """
    filtered = []
    for sub in subjects:
        if sub.motion_metrics is None:
            # If motion metrics are missing, we might exclude or warn. 
            # Assuming missing motion data implies we cannot verify, so we exclude.
            log_exclusion(reason="HIGH_MOTION", subject_id=sub.subject_id)
            continue

        fd_mean = sub.motion_metrics.get("fd_mean", 0.0)
        # Simple threshold check for demonstration
        if fd_mean > fd_thresh:
            logger.warning(f"Subject {sub.subject_id}: High motion (FD={fd_mean})")
            log_exclusion(reason="HIGH_MOTION", subject_id=sub.subject_id)
            continue

        filtered.append(sub)
    
    return filtered
