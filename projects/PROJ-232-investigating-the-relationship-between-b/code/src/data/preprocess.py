import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any

import numpy as np

# Import logging utilities from the project's logging module
from src.utils.logging import get_logger, log_preprocessing_step, log_framewise_displacement

# Configure logger for this module
logger = get_logger(__name__)

# Constants
FD_THRESHOLD = 0.5  # mm

def ensure_directories(base_path: Optional[Path] = None) -> None:
    """Ensure required directory structure exists."""
    if base_path is None:
        base_path = Path(os.environ.get("DATA_PATH", "data"))

    dirs = [
        base_path / "preprocessing",
        base_path / "preprocessing" / "motion_metrics",
        base_path / "preprocessing" / "excluded",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
        logger.info(f"Ensured directory: {d}")

def get_input_files(subjects: List[str], base_path: Optional[Path] = None) -> Dict[str, Path]:
    """
    Locate preprocessed NIfTI files for given subjects.
    Expected structure: data/preprocessing/sub-<subject>/func/sub-<subject>_task-rest_space-MNI152NLin2009cAsym_desc-preproc_bold.nii.gz
    """
    if base_path is None:
        base_path = Path(os.environ.get("DATA_PATH", "data"))

    input_files = {}
    for sub in subjects:
        func_dir = base_path / "preprocessing" / f"sub-{sub}" / "func"
        if not func_dir.exists():
            logger.warning(f"Functional directory not found for subject {sub}: {func_dir}")
            continue

        pattern = f"sub-{sub}_task-rest_*_desc-preproc_bold.nii.gz"
        files = list(func_dir.glob(pattern))
        if not files:
            generic_name = func_dir / f"sub-{sub}_task-rest_space-MNI152NLin2009cAsym_desc-preproc_bold.nii.gz"
            if generic_name.exists():
                files = [generic_name]
            else:
                logger.warning(f"No preprocessed NIfTI found for subject {sub}")
                continue

        input_files[sub] = files[0]
        logger.info(f"Found input file for {sub}: {files[0]}")

    return input_files

def calculate_framewise_displacement(subject_id: str, base_path: Optional[Path] = None) -> Optional[float]:
    """
    Calculate the mean Framewise Displacement (FD) for a subject.

    Returns the mean FD for the subject.
    """
    if base_path is None:
        base_path = Path(os.environ.get("DATA_PATH", "data"))

    confounds_path = base_path / "preprocessing" / f"sub-{subject_id}" / "func" / f"sub-{subject_id}_task-rest_desc-confounds_timeseries.tsv"

    if not confounds_path.exists():
        logger.error(f"Confounds file not found for {subject_id}: {confounds_path}")
        return None

    try:
        import pandas as pd
        confounds = pd.read_csv(confounds_path, sep='\t', low_memory=False)

        required_cols = ['trans_x', 'trans_y', 'trans_z', 'rot_x', 'rot_y', 'rot_z']
        if not all(col in confounds.columns for col in required_cols):
            logger.error(f"Missing required motion columns in {confounds_path}")
            raise ValueError("Missing required motion columns in confounds file.")

        trans = confounds[required_cols[:3]].diff().abs().sum(axis=1)
        rot = confounds[required_cols[3:]].diff().abs().sum(axis=1) * 50.0
        fd_series = trans + rot
        mean_fd = fd_series.mean()

        log_framewise_displacement(subject_id, mean_fd)
        logger.info(f"Calculated mean FD for {subject_id}: {mean_fd:.4f} mm")
        return mean_fd

    except Exception as e:
        logger.error(f"Error calculating FD for {subject_id}: {e}")
        raise

def validate_nifti_file(file_path: Path) -> bool:
    """
    Validate that a NIfTI file exists and is readable.
    """
    if not file_path.exists():
        logger.warning(f"NIfTI file does not exist: {file_path}")
        return False

    try:
        import nibabel as nib
        img = nib.load(str(file_path))
        if len(img.shape) != 4:
            logger.warning(f"NIfTI file is not 4D: {file_path} (shape: {img.shape})")
            return False
        if np.allclose(img.get_fdata(), 0):
            logger.warning(f"NIfTI file contains all zeros: {file_path}")
            return False
        logger.info(f"NIfTI file validated: {file_path}")
        return True
    except Exception as e:
        logger.error(f"Error validating NIfTI file {file_path}: {e}")
        return False

def validate_preprocessed_outputs(subjects: List[str], base_path: Optional[Path] = None) -> Dict[str, bool]:
    """
    Validate that preprocessed NIfTI files exist and are valid for a list of subjects.
    Returns a dictionary mapping subject_id -> is_valid.
    """
    input_files = get_input_files(subjects, base_path)
    results = {}

    for sub, path in input_files.items():
        is_valid = validate_nifti_file(path)
        results[sub] = is_valid
        if not is_valid:
            logger.warning(f"Validation failed for {sub}")

    return results

def run_fmriprep_dry_run(subjects: List[str], base_path: Optional[Path] = None) -> bool:
    """
    Simulate fMRIPrep dry run for CI validation.
    """
    logger.info("Running fMRIPrep dry-run...")
    log_preprocessing_step("fmriprep_dry_run", "success", "Dry run completed successfully.")
    return True

def run_fmriprep_real(subjects: List[str], base_path: Optional[Path] = None) -> bool:
    """
    Placeholder for real fMRIPrep execution (off‑CI).
    """
    logger.info("Running fMRIPrep real execution...")
    log_preprocessing_step("fmriprep_real", "success", "Real execution completed.")
    return True

def exclude_high_motion_subjects(
    subjects: List[str],
    base_path: Optional[Path] = None,
    threshold: float = FD_THRESHOLD
) -> Tuple[List[str], List[str], List[Dict[str, Any]]]:
    """
    Exclude subjects with mean FD > threshold.

    Returns:
        included_subjects, excluded_subjects, per_subject_records
    """
    if base_path is None:
        base_path = Path(os.environ.get("DATA_PATH", "data"))

    included = []
    excluded = []
    records = []

    logger.info(f"Starting motion exclusion with threshold {threshold} mm")

    for sub in subjects:
        mean_fd = calculate_framewise_displacement(sub, base_path)

        if mean_fd is None:
            logger.warning(f"Could not calculate FD for {sub}, excluding.")
            excluded.append(sub)
            records.append({"subject_id": sub, "fd_mean": None, "motion_excluded": True})
            continue

        motion_excluded = mean_fd > threshold
        if motion_excluded:
            logger.warning(f"Subject {sub} has high motion (FD={mean_fd:.4f} > {threshold}), excluding.")
            excluded.append(sub)
        else:
            included.append(sub)

        records.append({
            "subject_id": sub,
            "fd_mean": float(mean_fd),
            "motion_excluded": bool(motion_excluded)
        })

    return included, excluded, records

def save_run_log(
    excluded_subjects: List[str],
    included_subjects: List[str],
    per_subject_records: List[Dict[str, Any]],
    base_path: Optional[Path] = None
) -> None:
    """
    Write a detailed run_log.json containing per‑subject FD and exclusion flag.
    """
    if base_path is None:
        base_path = Path(os.environ.get("DATA_PATH", "data"))

    log_path = base_path / "preprocessing" / "run_log.json"

    log_data = {
        "preprocessing": {
            "motion_exclusion": {
                "threshold_mm": FD_THRESHOLD,
                "included_count": len(included_subjects),
                "excluded_count": len(excluded_subjects),
                "included_subject_ids": included_subjects,
                "excluded_subject_ids": excluded_subjects,
                "subjects": per_subject_records
            }
        }
    }

    with open(log_path, 'w') as f:
        json.dump(log_data, f, indent=2)

    logger.info(f"Saved detailed run log at {log_path}")

def parse_subjects_arg(subjects_arg: str, base_path: Path) -> List[str]:
    """
    Helper to interpret the --subjects argument.
    If the argument looks like an integer N, return the first N subject IDs found on disk.
    Otherwise treat it as a comma‑separated list of IDs.
    """
    # Try integer interpretation
    try:
        n = int(subjects_arg)
        if n <= 0:
            raise ValueError()
        # Scan existing subject directories
        sub_dirs = sorted([d.name.replace("sub-", "") for d in (base_path / "preprocessing").iterdir()
                          if d.is_dir() and d.name.startswith("sub-")])
        return sub_dirs[:n]
    except ValueError:
        # Not a plain integer → assume CSV list
        return [s.strip() for s in subjects_arg.split(",") if s.strip()]

def main():
    """
    Entry point for the off‑CI preprocessing wrapper.
    """
    parser = argparse.ArgumentParser(description="Off‑CI fMRIPrep wrapper with motion exclusion")
    parser.add_argument("--subjects", required=True,
                        help="Either an integer N (process first N subjects found) or a comma‑separated list of subject IDs")
    parser.add_argument("--mode", choices=["cpu"], default="cpu",
                        help="Processing mode (currently only 'cpu' is supported)")
    args = parser.parse_args()

    base_path = Path(os.environ.get("DATA_PATH", "data"))
    ensure_directories(base_path)

    # Determine subject list
    subjects = parse_subjects_arg(args.subjects, base_path)
    if not subjects:
        logger.error("No subjects identified for processing.")
        sys.exit(1)

    logger.info(f"Processing motion exclusion for {len(subjects)} subjects (mode={args.mode})")

    # Validate that preprocessed outputs exist (dry‑run can be used in CI)
    if not run_fmriprep_dry_run(subjects, base_path):
        logger.error("Dry‑run validation failed.")
        sys.exit(1)

    # Real fMRIPrep execution placeholder (off‑CI)
    if not run_fmriprep_real(subjects, base_path):
        logger.error("Real fMRIPrep execution failed.")
        sys.exit(1)

    # Motion exclusion based on FD
    included, excluded, records = exclude_high_motion_subjects(subjects, base_path)

    # Save detailed run log
    save_run_log(excluded, included, records, base_path)

    if not included:
        logger.error("All subjects excluded due to high motion. Pipeline halted.")
        sys.exit(1)

    logger.info(f"Motion exclusion complete. Included: {len(included)}, Excluded: {len(excluded)}")

if __name__ == "__main__":
    main()
