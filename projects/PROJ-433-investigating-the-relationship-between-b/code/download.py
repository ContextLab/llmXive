"""
HCP Data Download and Availability Verification Module.

Handles fetching HCP resting-state fMRI and behavioral datasets,
checking file availability, and managing data status without raising
exceptions for missing data (graceful handling).
"""
import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Import from local project modules (as per API surface)
from utils import setup_logger

# Configuration
# Based on typical HCP directory structure for resting-state fMRI
# Adjusted to match project data paths: data/raw/hcp/...
HCP_DATA_ROOT = Path("data/raw")
FMRI_SUBFOLDER_PATTERN = "MNINonLinear/Results/r{task}"
TASK_REST = "r11100"  # HCP resting state task identifier
FILE_PATTERN = "rfMRI_REST1_LR.nii.gz"


def verify_fMRI_availability(subject_id: str) -> Dict[str, Any]:
    """
    Check for the existence of fMRI time-series files for a given subject.

    This function checks the local filesystem for the expected pre-processed
    or raw fMRI time-series files corresponding to the HCP dataset structure.
    It does NOT raise exceptions if data is missing; instead, it returns a
    status dictionary allowing the caller to handle the "Data Gap" gracefully.

    Args:
        subject_id (str): The HCP subject ID (e.g., '100307').

    Returns:
        dict: A status object with one of the following structures:
              {'status': 'PRESENT'}
              {'status': 'MISSING', 'reason': 'Data Gap: fMRI time-series not found'}
    """
    logger = setup_logger()

    # Construct the expected path based on HCP directory structure
    # Typical HCP path: data/raw/<subject_id>/MNINonLinear/Results/r11100/rfMRI_REST1_LR.nii.gz
    expected_file = (
        HCP_DATA_ROOT
        / subject_id
        / "MNINonLinear"
        / "Results"
        / TASK_REST
        / FILE_PATTERN
    )

    logger.info(f"Checking fMRI availability for subject {subject_id} at: {expected_file}")

    if expected_file.exists():
        logger.info(f"fMRI data found for subject {subject_id}.")
        return {'status': 'PRESENT'}
    else:
        reason = "Data Gap: fMRI time-series not found"
        logger.warning(f"fMRI data MISSING for subject {subject_id}. {reason}")
        return {'status': 'MISSING', 'reason': reason}


def check_dataset_status(subject_ids: list) -> Dict[str, Dict[str, Any]]:
    """
    Batch check availability for multiple subjects.

    Args:
        subject_ids (list): List of subject IDs to check.

    Returns:
        dict: Mapping of subject_id -> status object.
    """
    results = {}
    for sid in subject_ids:
        results[sid] = verify_fMRI_availability(sid)
    return results


if __name__ == "__main__":
    # Simple CLI entry point for testing availability
    # Usage: python -m code.download --subject 100307
    import argparse

    parser = argparse.ArgumentParser(description="Verify fMRI data availability")
    parser.add_argument("--subject", type=str, required=True, help="Subject ID to check")
    args = parser.parse_args()

    status = verify_fMRI_availability(args.subject)
    print(f"Subject {args.subject}: {status}")
