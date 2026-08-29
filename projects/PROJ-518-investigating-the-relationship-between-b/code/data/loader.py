import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, NamedTuple
from dataclasses import dataclass
from errors import DataMissingCreativityError
from utils.logging import log_exclusion
from config import get_config

@dataclass
class Participant:
    subject_id: str
    fmri_path: Optional[str]
    behavioral_data: Dict[str, Any]
    fd_mean: float = 0.0
    fd_max: float = 0.0
    high_motion_volumes_ratio: float = 0.0

def validate_caq_availability(manifest_path: str, behavioral_path: str) -> bool:
    config = get_config()
    if not os.path.exists(manifest_path):
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")
    
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)
    
    if 'caq_score' not in manifest:
        raise DataMissingCreativityError("Missing CAQ field in manifest")
    
    if not os.path.exists(behavioral_path):
        raise FileNotFoundError(f"Behavioral data not found: {behavioral_path}")
    
    return True

def fetch_hcp_data(subject_id: str) -> Dict[str, Any]:
    config = get_config()
    data_path = Path(config.DATA_PATH)
    fmri_file = data_path / f"{subject_id}_bold.nii.gz"
    behavior_file = data_path / f"{subject_id}_behavior.json"
    
    if not fmri_file.exists():
        raise FileNotFoundError(f"fMRI data not found for {subject_id}")
    
    if not behavior_file.exists():
        raise FileNotFoundError(f"Behavioral data not found for {subject_id}")
    
    with open(behavior_file, 'r') as f:
        behavior_data = json.load(f)
    
    return {
        'fmri_path': str(fmri_file),
        'behavioral_data': behavior_data
    }

def validate_and_filter_subjects(subjects: List[Participant]) -> List[Participant]:
    filtered = []
    for sub in subjects:
        if not sub.fmri_path or not os.path.exists(sub.fmri_path):
            log_exclusion("MISSING_SCAN", sub.subject_id)
            continue
        
        if not sub.behavioral_data or 'caq_score' not in sub.behavioral_data:
            log_exclusion("MISSING_SCORE", sub.subject_id)
            continue
        
        filtered.append(sub)
    
    return filtered

def filter_by_motion(subjects: List[Participant], fd_thresh: float = 0.5, vol_thresh: float = 0.2) -> List[Participant]:
    """
    Exclude participants exceeding motion criteria and log the exclusion.
    
    Args:
        subjects: List of Participant objects with motion metrics.
        fd_thresh: Threshold for mean Framewise Displacement (default 0.5).
        vol_thresh: Threshold for high motion volumes ratio (default 0.2).
    
    Returns:
        List of participants passing motion criteria.
    """
    filtered = []
    for sub in subjects:
        # Check mean FD threshold
        if sub.fd_mean > fd_thresh:
            log_exclusion("HIGH_MOTION", sub.subject_id, reason=f"Mean FD {sub.fd_mean:.4f} > {fd_thresh}")
            continue
        
        # Check high motion volumes ratio
        if sub.high_motion_volumes_ratio > vol_thresh:
            log_exclusion("HIGH_MOTION", sub.subject_id, reason=f"High motion vol ratio {sub.high_motion_volumes_ratio:.4f} > {vol_thresh}")
            continue
        
        filtered.append(sub)
    
    return filtered
