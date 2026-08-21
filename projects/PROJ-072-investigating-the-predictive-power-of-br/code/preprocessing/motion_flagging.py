"""
Motion Flagging Module for User Story 1.

This module implements the logic to exclude subjects with excessive head motion
(>2mm translation) from the analysis pipeline. It reads motion parameters from
the preprocessed data directory, calculates maximum displacement, and updates
the subject status metadata file.
"""
import os
import sys
import csv
import json
import logging
import numpy as np
from pathlib import Path

# Project root configuration
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DATA_METADATA_DIR = PROJECT_ROOT / "data" / "metadata"
SUBJECT_STATUS_FILE = DATA_METADATA_DIR / "subject_status.csv"
EXCLUSION_LOG_FILE = DATA_METADATA_DIR / "exclusion_log.txt"

# Motion threshold in mm
MOTION_THRESHOLD_MM = 2.0

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_all_subject_ids() -> list:
    """
    Scans the raw data directory for available subject folders.
    Assumes directory structure: data/raw/ds000030/sub-<id>/

    Returns:
        List of subject IDs (e.g., ['sub-01', 'sub-02'])
    """
    if not DATA_RAW_DIR.exists():
        logger.warning(f"Data raw directory not found: {DATA_RAW_DIR}")
        return []

    # Look for sub- folders directly in the dataset root or inside ds000030
    # OpenNeuro ds000030 structure is typically: data/raw/ds000030/sub-XXX/
    dataset_root = DATA_RAW_DIR / "ds000030"
    if not dataset_root.exists():
        # Fallback if dataset is extracted directly to data/raw
        dataset_root = DATA_RAW_DIR

    subject_dirs = [d for d in dataset_root.iterdir() if d.is_dir() and d.name.startswith("sub-")]
    return [d.name for d in sorted(subject_dirs)]


def load_motion_parameters(subject_id: str) -> np.ndarray:
    """
    Loads motion parameters (6 rigid body parameters: 3 translation, 3 rotation)
    for a specific subject.

    The motion parameters are typically stored in a .tsv or .txt file generated
    during preprocessing (e.g., from FSL MCFLIRT or similar).
    Expected file pattern: sub-<id>_motion_params.tsv

    Args:
        subject_id: The subject ID string (e.g., 'sub-01')

    Returns:
        numpy array of shape (n_timepoints, 6) containing motion parameters.
        Translation is in mm, rotation in radians.

    Raises:
        FileNotFoundError: If the motion parameters file does not exist.
    """
    # Try to find the motion parameters file in the subject's raw directory
    subject_dir = DATA_RAW_DIR / "ds000030" / subject_id
    if not subject_dir.exists():
        subject_dir = DATA_RAW_DIR / subject_id

    # Look for common motion parameter file names
    possible_files = [
        subject_dir / f"{subject_id}_motion_params.tsv",
        subject_dir / f"{subject_id}_mc_params.tsv",
        subject_dir / "regressors.tsv", # Common nilearn/FSL output
        subject_dir / "confounds.tsv",
    ]

    motion_file = None
    for p in possible_files:
        if p.exists():
            motion_file = p
            break

    if motion_file is None:
        # If preprocessing hasn't generated motion params yet, we might need to
        # look in the processed directory or assume a placeholder.
        # However, per T012/T013, preprocessing should have run.
        # Let's check processed dir as a fallback for the specific output of T012
        processed_subject_dir = DATA_PROCESSED_DIR / subject_id
        if processed_subject_dir.exists():
            for p in processed_subject_dir.iterdir():
                if "motion" in p.name.lower() or "confound" in p.name.lower():
                    motion_file = p
                    break

    if motion_file is None:
        # If we still can't find it, we cannot calculate motion.
        # This implies the preprocessing step (T012) did not generate motion logs.
        # We raise an error to fail loudly as per constraints.
        raise FileNotFoundError(
            f"Motion parameters file not found for {subject_id}. "
            f"Searched in: {subject_dir} and {processed_subject_dir}. "
            f"Ensure T012 (preprocess.py) generates motion logs."
        )

    # Load the file
    try:
        # Assuming TSV or CSV with 6 columns (3 trans, 3 rot)
        # If headers exist, we skip them or use pandas
        import pandas as pd
        df = pd.read_csv(motion_file, sep='\t')

        # Identify columns. Usually named trans_x, trans_y, trans_z, rot_x, rot_y, rot_z
        # or just 6 columns.
        if df.shape[1] < 6:
            logger.warning(f"Motion file {motion_file} has fewer than 6 columns. Skipping subject {subject_id}.")
            return np.array([])

        # Select first 6 columns if more exist, or specific columns if named
        # Standardizing on first 6 for robustness if names vary
        params_df = df.iloc[:, :6]
        return params_df.values.astype(float)
    except Exception as e:
        logger.error(f"Failed to parse motion parameters for {subject_id}: {e}")
        raise


def calculate_max_displacement(motion_params: np.ndarray) -> float:
    """
    Calculates the maximum translation displacement (in mm) for a subject.

    The first 3 columns are assumed to be translation (x, y, z) in mm.
    Rotation is ignored for the >2mm translation threshold check as per task description.

    Args:
        motion_params: numpy array of shape (n_timepoints, 6)

    Returns:
        Maximum translation displacement in mm.
    """
    if motion_params.size == 0:
        return 0.0

    translations = motion_params[:, :3]
    # Calculate Euclidean distance from origin (0,0,0) for each timepoint
    # Or max absolute difference from mean? Usually max absolute displacement from origin or baseline.
    # Standard practice: max absolute value of any translation parameter, or max displacement from first frame.
    # Task says ">2mm translation". We interpret this as max absolute translation value across all timepoints.
    max_trans = np.max(np.abs(translations))
    return float(max_trans)


def flag_subject_motion(subject_id: str) -> dict:
    """
    Evaluates a single subject for motion artifacts.

    Args:
        subject_id: Subject ID string.

    Returns:
        Dictionary with keys:
            - 'subject_id': str
            - 'excluded': bool
            - 'reason': str (empty if included)
            - 'max_displacement': float (mm)
    """
    try:
        params = load_motion_parameters(subject_id)
        max_disp = calculate_max_displacement(params)
    except FileNotFoundError as e:
        logger.warning(str(e))
        # If we can't load motion, we might exclude or keep?
        # Strictly, we can't verify, so we exclude to be safe or log as error.
        # Let's exclude and flag as 'missing_motion_data'.
        return {
            'subject_id': subject_id,
            'excluded': True,
            'reason': 'missing_motion_data',
            'max_displacement': np.nan
        }

    excluded = max_disp > MOTION_THRESHOLD_MM
    reason = ""
    if excluded:
        reason = f"excessive_motion (> {MOTION_THRESHOLD_MM}mm, max={max_disp:.3f}mm)"

    return {
        'subject_id': subject_id,
        'excluded': excluded,
        'reason': reason,
        'max_displacement': max_disp
    }


def run_motion_flagging_pipeline() -> None:
    """
    Main pipeline function to process all subjects, flag motion, and update metadata.

    1. Gets all subject IDs.
    2. Flags each subject for motion.
    3. Updates `data/metadata/subject_status.csv`.
    4. Updates `data/metadata/exclusion_log.txt` with the count of excluded subjects.
    """
    logger.info("Starting motion flagging pipeline...")

    subject_ids = get_all_subject_ids()
    if not subject_ids:
        logger.warning("No subjects found to process.")
        return

    results = []
    excluded_count = 0
    excluded_subjects = []

    # Ensure metadata directory exists
    DATA_METADATA_DIR.mkdir(parents=True, exist_ok=True)

    for sub_id in subject_ids:
        status = flag_subject_motion(sub_id)
        results.append(status)
        if status['excluded']:
            excluded_count += 1
            excluded_subjects.append(sub_id)

    # Write subject_status.csv
    # Columns: subject_id, excluded, reason, max_displacement
    status_file_path = SUBJECT_STATUS_FILE
    with open(status_file_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['subject_id', 'excluded', 'reason', 'max_displacement'])
        writer.writeheader()
        for res in results:
            writer.writerow(res)

    logger.info(f"Updated subject status file: {status_file_path}")

    # Write exclusion_log.txt (Append mode to preserve history if run multiple times, or overwrite?)
    # Task says "update ... with exclusion count". Let's append a summary line.
    exclusion_log_path = EXCLUSION_LOG_FILE
    with open(exclusion_log_path, 'a') as f:
        f.write(f"Motion Flagging Run: {len(subject_ids)} subjects processed, {excluded_count} excluded.\n")
        if excluded_subjects:
            f.write(f"Excluded subjects: {', '.join(excluded_subjects)}\n")
        f.write("-" * 40 + "\n")

    logger.info(f"Exclusion log updated: {exclusion_log_path}. Excluded: {excluded_count}")


def main():
    """Entry point for script execution."""
    run_motion_flagging_pipeline()


if __name__ == "__main__":
    main()
