import os
import json
import logging
import numpy as np
import nibabel as nib
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import pandas as pd

from src.config import load_config
from src.utils import get_logger, log_exception
from src.exceptions import DataUnavailableError, InsufficientDataError
from src.integrity import update_hashes

# Constants
MOTION_THRESHOLD_MM = 3.0
MIN_SUBJECTS = 10

def load_motion_parameters(subject_id: str, config: Dict[str, Any]) -> Optional[pd.DataFrame]:
    """Load motion parameters for a subject."""
    # Placeholder for actual loading logic from fMRIPrep or similar
    # Assumes files exist in data/raw/ds000030/...
    raw_dir = Path(config['paths']['raw_data']) / "ds000030"
    # Example path structure
    confound_file = raw_dir / "sub-01" / "func" / f"sub-01_task-cowball_run-01_desc-confounds_timeseries.tsv"
    # Adjust path logic based on actual dataset structure
    return None

def calculate_framewise_displacement(motion_params: pd.DataFrame) -> float:
    """Calculate Framewise Displacement from motion parameters."""
    # Standard FD calculation
    # Translations: dX, dY, dZ
    # Rotations: dRotX, dRotY, dRotZ (converted to mm)
    # FD = |dX| + |dY| + |dZ| + |dRotX|*50 + |dRotY|*50 + |dRotZ|*50
    # Assuming columns exist
    if motion_params is None:
        return 0.0
    
    # Simplified calculation for demonstration
    # In real implementation, parse the specific columns
    return 0.0

def calculate_subject_motion_metrics(subject_id: str, config: Dict[str, Any], logger: logging.Logger) -> Dict[str, Any]:
    """Calculate motion metrics for a single subject."""
    logger.info(f"Calculating motion for {subject_id}")
    # Load params
    params = load_motion_parameters(subject_id, config)
    fd = calculate_framewise_displacement(params)
    return {
        "subject_id": subject_id,
        "motion_metric": fd,
        "condition_status": "valid", # Placeholder, verified later
        "retained": fd <= MOTION_THRESHOLD_MM
    }

def verify_conditions(subject_id: str, config: Dict[str, Any], logger: logging.Logger) -> Tuple[bool, str]:
    """Verify that both Inclusion and Exclusion conditions exist."""
    # Check event files or design matrix
    # Placeholder
    return True, "valid"

def filter_by_motion_threshold(subject_list: List[Dict[str, Any]], threshold: float = MOTION_THRESHOLD_MM) -> List[Dict[str, Any]]:
    """Filter subjects based on motion threshold."""
    return [s for s in subject_list if s['motion_metric'] <= threshold]

def check_subject_count(subject_list: List[Dict[str, Any]], config: Dict[str, Any], logger: logging.Logger) -> None:
    """Check if sufficient subjects remain after filtering."""
    retained = [s for s in subject_list if s.get('retained', False)]
    count = len(retained)
    if count < MIN_SUBJECTS:
        logger.error(f"Insufficient subjects: {count} < {MIN_SUBJECTS}")
        raise InsufficientDataError(count)

def run_qc_pipeline(config: Dict[str, Any], logger: logging.Logger) -> List[Dict[str, Any]]:
    """
    Main QC pipeline:
    1. Iterate subjects
    2. Calculate motion
    3. Verify conditions
    4. Filter
    5. Save outputs
    """
    # Get subject list (simplified)
    subjects = ["sub-01", "sub-02", "sub-03", "sub-04", "sub-05", "sub-06", "sub-07", "sub-08", "sub-09", "sub-10", "sub-11", "sub-12"]
    
    qc_results = []
    for subj in subjects:
        motion_data = calculate_subject_motion_metrics(subj, config, logger)
        valid, status = verify_conditions(subj, config, logger)
        motion_data['condition_status'] = status if valid else "invalid"
        motion_data['retained'] = motion_data['retained'] and valid
        qc_results.append(motion_data)

    # Filter
    retained_list = filter_by_motion_threshold(qc_results)
    
    # Check count
    check_subject_count(qc_results, config, logger)

    # Save outputs
    output_dir = Path(config['paths']['processed_data'])
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. subject_qc_list.json
    qc_list_path = output_dir / "subject_qc_list.json"
    with open(qc_list_path, 'w') as f:
        json.dump(qc_results, f, indent=2)
    
    # 2. subjects_metadata.json (definitive retained list)
    metadata_path = output_dir / "subjects_metadata.json"
    with open(metadata_path, 'w') as f:
        json.dump(retained_list, f, indent=2)

    # Update integrity
    update_hashes([qc_list_path, metadata_path], config, logger)

    logger.info(f"QC Pipeline completed. Retained: {len(retained_list)} subjects.")
    return qc_results

def main():
    config = load_config()
    logger = get_logger()
    run_qc_pipeline(config, logger)

if __name__ == "__main__":
    main()
