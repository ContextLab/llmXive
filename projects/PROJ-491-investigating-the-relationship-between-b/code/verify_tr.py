"""
Task T017: Verify TR of downloaded data matches expected values.

This script scans the downloaded NIfTI files in data/raw/ to verify that
the Repetition Time (TR) matches the expected value defined in config.py.
If a mismatch is found, it exits with code 1 and prints "Error: TR mismatch".
"""
import os
import sys
import logging
import numpy as np
import nibabel as nib
from pathlib import Path

from config import ensure_directories
from streaming_utils import get_nifti_volume_info

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/processed/tr_verification.log')
    ]
)
logger = logging.getLogger(__name__)

def get_expected_tr():
    """
    Retrieve the expected TR from config.py.
    We assume the config defines a standard TR for the HCP task data.
    If not explicitly defined as a constant, we default to 0.72s (HCP standard)
    but prefer reading from a central config if available.
    """
    # Attempt to import a specific TR constant if defined in config
    try:
        # Check if config has an explicit TR setting
        import code.config as cfg
        if hasattr(cfg, 'EXPECTED_TR'):
            return cfg.EXPECTED_TR
    except (ImportError, AttributeError):
        pass

    # Fallback: HCP task-fMRI standard TR is 0.72s
    # Resting-state is often 0.72s as well in HCP.
    # We will use 0.72 as the primary expected value.
    return 0.72

def verify_subject_tr(subject_dir, expected_tr, tolerance=0.01):
    """
    Verify TR for all NIfTI files in a subject directory.
    Returns (is_valid, mismatched_files, msg).
    """
    nifti_files = list(subject_dir.glob('*.nii.gz')) + list(subject_dir.glob('*.nii'))
    if not nifti_files:
        return False, [], f"No NIfTI files found in {subject_dir}"

    mismatches = []
    for nifti_path in nifti_files:
        try:
            # Use streaming utility to get volume info efficiently
            # This function returns (shape, zooms, data_dtype) or similar
            # We need the TR specifically. NIfTI header 'pixdim' contains TR at index 4.
            img = nib.load(str(nifti_path))
            header = img.header
            # TR is typically the 5th element in pixdim (index 4)
            # pixdim: [1, x, y, z, t, ...]
            # Note: nibabel header.pixdim returns a 1D array
            tr = header.get_zooms()[3] # index 3 corresponds to time dimension in 4D

            if abs(tr - expected_tr) > tolerance:
                mismatches.append({
                    'file': str(nifti_path),
                    'found_tr': tr,
                    'expected_tr': expected_tr
                })
        except Exception as e:
            logger.error(f"Error reading {nifti_path}: {e}")
            return False, [], f"Error reading file {nifti_path}: {e}"

    if mismatches:
        msg = f"TR mismatch detected in {subject_dir}: {len(mismatches)} files."
        return False, mismatches, msg

    return True, [], "OK"

def main():
    ensure_directories()
    data_raw_path = Path('data/raw')
    expected_tr = get_expected_tr()

    logger.info(f"Starting TR verification. Expected TR: {expected_tr}s")

    if not data_raw_path.exists():
        logger.error("data/raw directory not found. Has data ingestion run?")
        print("Error: TR mismatch") # Requirement: specific error message on fail
        sys.exit(1)

    subject_dirs = [d for d in data_raw_path.iterdir() if d.is_dir()]
    if not subject_dirs:
        logger.warning("No subject directories found in data/raw.")
        # If no data, we can't verify, but strictly speaking the task is about
        # verifying *downloaded* data. If none exists, it's a data ingestion issue.
        # However, T017 is a check. If no data, we can't confirm TR.
        # We will treat this as a failure to verify.
        print("Error: TR mismatch")
        sys.exit(1)

    all_valid = True
    total_checked = 0
    total_mismatched = 0

    for subject_dir in subject_dirs:
        total_checked += 1
        is_valid, mismatches, msg = verify_subject_tr(subject_dir, expected_tr)
        
        if is_valid:
            logger.info(f"Subject {subject_dir.name}: {msg}")
        else:
            logger.error(f"Subject {subject_dir.name}: {msg}")
            for m in mismatches:
                logger.error(f"  - {m['file']}: Found {m['found_tr']}s, Expected {m['expected_tr']}s")
            all_valid = False
            total_mismatched += 1

    logger.info(f"Verification complete. Checked {total_checked} subjects. Mismatches: {total_mismatched}")

    if not all_valid:
        print("Error: TR mismatch")
        sys.exit(1)

    logger.info("All subjects passed TR verification.")
    sys.exit(0)

if __name__ == '__main__':
    main()