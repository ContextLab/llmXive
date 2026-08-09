"""
Download and verification utilities for HCP fMRI data.
"""
import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional

from utils import setup_logger

# Configuration
DATA_ROOT = Path("data")
RAW_DATA_DIR = DATA_ROOT / "raw"
LOG_FILE = DATA_ROOT / "preprocess_log.txt"

def verify_fMRI_availability(subject_id: str) -> Dict[str, Any]:
    """
    Check for existence of fMRI time-series files for a given subject.

    Args:
        subject_id (str): The HCP subject ID.

    Returns:
        dict: Status object with 'status' key ('PRESENT' or 'MISSING').
              If MISSING, includes a 'reason' key.
    """
    logger = setup_logger()
    
    # Define expected path structure for HCP data (simplified for verification)
    # In a real scenario, this would check the specific HCP directory structure
    # e.g., data/raw/HCP1200/<subject_id>/MNINonLinear/Results/...
    expected_base = RAW_DATA_DIR / "HCP1200" / subject_id / "MNINonLinear" / "Results"
    
    # Check if the base directory exists
    if not expected_base.exists():
        logger.warning(f"Data Gap: fMRI time-series not found for subject {subject_id} at {expected_base}")
        return {
            'status': 'MISSING',
            'reason': f'Data Gap: fMRI time-series not found for subject {subject_id}'
        }

    # Check for specific resting state files (e.g., rfMRI_REST1_LR)
    # HCP typically has rfMRI_REST1_LR, rfMRI_REST1_RL, rfMRI_REST2_LR, rfMRI_REST2_RL
    required_files = [
        "rfMRI_REST1_LR_hp2000_clean.nii.gz",
        "rfMRI_REST1_RL_hp2000_clean.nii.gz"
    ]
    
    missing_files = []
    for fname in required_files:
        if not (expected_base / fname).exists():
            missing_files.append(fname)

    if missing_files:
        logger.warning(f"Data Gap: Missing files for subject {subject_id}: {missing_files}")
        return {
            'status': 'MISSING',
            'reason': f'Data Gap: fMRI time-series not found for subject {subject_id} (Missing: {", ".join(missing_files)})'
        }

    logger.info(f"fMRI data verified for subject {subject_id}")
    return {'status': 'PRESENT'}

def check_dataset_status(dataset_name: str) -> Dict[str, Any]:
    """
    Check the general status of a dataset directory.

    Args:
        dataset_name (str): Name of the dataset (e.g., 'HCP1200').

    Returns:
        dict: Status information.
    """
    logger = setup_logger()
    dataset_path = RAW_DATA_DIR / dataset_name
    
    if not dataset_path.exists():
        return {
            'status': 'MISSING',
            'path': str(dataset_path),
            'reason': 'Dataset directory does not exist'
        }
    
    return {
        'status': 'PRESENT',
        'path': str(dataset_path),
        'reason': 'Dataset directory exists'
    }
